#!/usr/bin/env bash
# Weekly founding-members progress digest for Intent Solutions Learn (NOW-LMS).
#
# now-lms-owned copy (moved from intent-os 2026-07-29, owner order) with the
# post-rollout audit findings fixed:
#   * Covers the WHOLE active cohort, admins included — the old tipo='student'
#     filter silently dropped 5 of the 49 founding members (the lead admins).
#     System accounts are excluded via LMS_DIGEST_EXCLUDE (default: intentadmin).
#   * Read-only is ENFORCED server-side (PGOPTIONS default_transaction_read_only),
#     not just promised by the function name.
#
# Builds a per-member HTML table (role, last access, enrollments, progress,
# completions, certificates) plus the "touched nothing yet" list, and mails it
# to the owner + leads via the estate sender (send-email.cjs on MXroute SMTP;
# creds decrypted in-process from the prod sops file — never written to disk).
#
# Usage:
#   lms-progress-digest.sh [--dry-run] [--to addr]...
#     --dry-run   print the report to stdout, send nothing
#     --to        override the recipient list (repeatable)
#
# Cron (dev box, deployed copy — never the working tree):
#   source PATH self-sufficiency, then this script; failures page via
#   ~/bin/lib/notify-lib.sh cron_fail when available.
set -euo pipefail
export PATH="$HOME/bin:/usr/local/bin:/usr/bin:/bin"

HOST="${LMS_HOST:-intentsolutions}"
DB_CONTAINER="${LMS_DB_CONTAINER:-now-lms-db-1}"
DB_USER="${LMS_DB_USER:-nowlms}"
DB_NAME="${LMS_DB_NAME:-nowlms}"
SENDER="${LMS_DIGEST_SENDER:-$HOME/.claude/skills/email/scripts/send-email.cjs}"
SOPS_FILE="${LMS_DIGEST_SOPS:-$HOME/000-projects/intent-os/ops/host/secrets/secrets.prod.sops.yaml}"
SMTP_HOST_DEFAULT="sunfire.mxrouting.net"
SMTP_PORT_DEFAULT="587"
# Comma-separated usernames excluded from the member table (system accounts).
EXCLUDE="${LMS_DIGEST_EXCLUDE:-intentadmin}"

DRY_RUN=0
RECIPIENTS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --to) shift; RECIPIENTS+=("$1") ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done
if [ ${#RECIPIENTS[@]} -eq 0 ]; then
  RECIPIENTS=(jeremy@intentsolutions.io)
fi

psql_ro() {
  # Read-only enforced at the server: default_transaction_read_only=on makes
  # any write in this session fail, regardless of what the query text says.
  # ssh joins argv into one remote shell string, so the query must be quoted.
  ssh "$HOST" "docker exec -e PGOPTIONS='-c default_transaction_read_only=on' $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -At -F '|' -c $(printf '%q' "$1")"
}

fail() {
  echo "lms-progress-digest FAILED: $1" >&2
  if [ -r "$HOME/bin/lib/notify-lib.sh" ] && [ "$DRY_RUN" -eq 0 ]; then
    # shellcheck source=/dev/null
    . "$HOME/bin/lib/notify-lib.sh" 2>/dev/null || true
    command -v cron_fail >/dev/null 2>&1 && cron_fail "lms-progress-digest" "$1" || true
  fi
  exit 1
}

# Build a quoted SQL IN-list from the comma-separated exclusion set.
EXCLUDE_SQL=$(printf '%s' "$EXCLUDE" | awk -F',' '{for(i=1;i<=NF;i++){gsub(/^ +| +$/,"",$i); if($i!="")printf "%s'\''%s'\''", (out++?",":""), $i}}')
[ -n "$EXCLUDE_SQL" ] || EXCLUDE_SQL="''"

MEMBERS=$(psql_ro "
  SELECT u.usuario,
         COALESCE(NULLIF(TRIM(COALESCE(u.nombre,'')||' '||COALESCE(u.apellido,'')),''), u.usuario),
         u.tipo,
         COALESCE(TO_CHAR(u.ultimo_acceso,'YYYY-MM-DD'),'never'),
         COALESCE(e.n,0)
  FROM usuario u
  LEFT JOIN (SELECT usuario, COUNT(*) n FROM estudiante_curso WHERE vigente GROUP BY usuario) e
    ON e.usuario = u.usuario
  WHERE u.activo AND u.usuario NOT IN ($EXCLUDE_SQL)
  ORDER BY u.ultimo_acceso DESC NULLS LAST, u.usuario;") || fail "members query"

PROGRESS=$(psql_ro "
  SELECT usuario, curso, recursos_completados, recursos_requeridos,
         ROUND(COALESCE(avance,0)::numeric,0), completado
  FROM curso_usuario_avance ORDER BY usuario, curso;") || fail "progress query"

CERTS=$(psql_ro "
  SELECT usuario, COALESCE(curso,'-'), TO_CHAR(fecha,'YYYY-MM-DD')
  FROM certificacion ORDER BY fecha DESC;") || fail "certs query"

UNTOUCHED=$(printf '%s\n' "$MEMBERS" | awk -F'|' '$4=="never"{print $2" <"$1">"}')
N_MEMBERS=$(printf '%s\n' "$MEMBERS" | /usr/bin/grep -c . || true)
N_UNTOUCHED=$(printf '%s\n' "$UNTOUCHED" | /usr/bin/grep -c . || true)
TODAY=$(date +%Y-%m-%d)

REPORT_HTML=$(mktemp)
trap 'rm -f "$REPORT_HTML"' EXIT
{
  echo "<h2 style='font-family:sans-serif'>Intent Solutions Learn — member progress digest ($TODAY)</h2>"
  echo "<p style='font-family:sans-serif'>$N_MEMBERS active members &middot; $N_UNTOUCHED have not logged in yet.</p>"
  echo "<h3 style='font-family:sans-serif'>Members</h3>"
  echo "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;font-family:sans-serif;font-size:13px'>"
  echo "<tr><th>Member</th><th>Role</th><th>Last access</th><th>Courses enrolled</th></tr>"
  [ -n "$MEMBERS" ] && printf '%s\n' "$MEMBERS" | awk -F'|' '{printf "<tr><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td><td>%s</td></tr>\n",$2,$1,$3,$4,$5}'
  echo "</table>"
  echo "<h3 style='font-family:sans-serif'>Per-course progress</h3>"
  if [ -n "$PROGRESS" ]; then
    echo "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;font-family:sans-serif;font-size:13px'>"
    echo "<tr><th>Member</th><th>Course</th><th>Done/Required</th><th>%</th><th>Completed</th></tr>"
    printf '%s\n' "$PROGRESS" | awk -F'|' '{printf "<tr><td>%s</td><td>%s</td><td>%s/%s</td><td>%s%%</td><td>%s</td></tr>\n",$1,$2,$3,$4,$5,$6}'
    echo "</table>"
  else
    echo "<p style='font-family:sans-serif'>No course activity recorded yet.</p>"
  fi
  echo "<h3 style='font-family:sans-serif'>Certificates issued</h3>"
  if [ -n "$CERTS" ]; then
    echo "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;font-family:sans-serif;font-size:13px'>"
    echo "<tr><th>Member</th><th>Course</th><th>Date</th></tr>"
    printf '%s\n' "$CERTS" | awk -F'|' '{printf "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n",$1,$2,$3}'
    echo "</table>"
  else
    echo "<p style='font-family:sans-serif'>None yet.</p>"
  fi
  if [ -n "$UNTOUCHED" ]; then
    echo "<h3 style='font-family:sans-serif'>Not logged in yet (nudge list)</h3><ul style='font-family:sans-serif;font-size:13px'>"
    printf '%s\n' "$UNTOUCHED" | sed 's/</\&lt;/g;s/>/\&gt;/g;s/^/<li>/;s/$/<\/li>/'
    echo "</ul>"
  fi
  echo "<p style='font-family:sans-serif;color:#777;font-size:12px'>Generated by ops/lms/lms-progress-digest.sh (read-only, server-enforced). Admin panel for live detail: https://learn.intentsolutions.io</p>"
} > "$REPORT_HTML"

if [ "$DRY_RUN" -eq 1 ]; then
  cat "$REPORT_HTML"
  exit 0
fi

command -v sops >/dev/null 2>&1 || fail "sops not on PATH"
[ -r "$SOPS_FILE" ] || fail "sops file missing: $SOPS_FILE"
SMTP_USER=$(sops -d "$SOPS_FILE" | awk '/^mxroute_jeremy_mailbox_user:/{print $2}') || fail "sops decrypt"
SMTP_PASS=$(sops -d "$SOPS_FILE" | awk '/^mxroute_jeremy_mailbox_password:/{print $2}') || fail "sops decrypt"
[ -n "$SMTP_USER" ] && [ -n "$SMTP_PASS" ] || fail "mxroute mailbox creds empty"

TO_ARGS=()
for r in "${RECIPIENTS[@]}"; do TO_ARGS+=(--to "$r"); done
SMTP_HOST="$SMTP_HOST_DEFAULT" SMTP_PORT="$SMTP_PORT_DEFAULT" \
SMTP_USER="$SMTP_USER" SMTP_PASS="$SMTP_PASS" \
  node "$SENDER" "${TO_ARGS[@]}" \
    --from jeremy@intentsolutions.io \
    --subject "Learn platform digest $TODAY — $N_MEMBERS members, $N_UNTOUCHED untouched" \
    --html "$REPORT_HTML" || fail "send"

echo "digest sent to: ${RECIPIENTS[*]}"
