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
# completions, certificates), the ranked most-missed-questions table, and the
# "touched nothing yet" list, then mails it to the owner + leads via the estate
# sender (send-email.cjs on MXroute SMTP; creds decrypted in-process from the
# prod sops file — never written to disk).
#
# The most-missed table is the content signal: it ranks questions by the share
# of submitted attempts that got them wrong, so lesson and video priorities come
# from measured confusion. Its grading logic mirrors
# now_lms/vistas/evaluations.py::_answer_is_correct — if that function changes,
# this query has to change with it.
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

# Ranked per-question miss rate. This is the content signal: which questions the
# cohort actually gets wrong, ordered, so the video and lesson backlog is set by
# measured confusion rather than by guesswork.
#
# Grading is replicated from now_lms/vistas/evaluations.py::_answer_is_correct
# and MUST stay in step with it:
#   * boolean  — correct iff exactly one option was selected and it is correct.
#   * multiple — correct iff the selected set EXACTLY equals the correct set.
#                Partial answers and supersets both score zero; there is no
#                partial credit.
#   * a null, empty, or non-array payload is a miss.
# The denominator is submitted attempts of the evaluation, not answer rows,
# because calculate_score divides by the question count — so a question a
# learner skipped is a miss for the score and is a miss here too. The `answered`
# column exposes that gap: answered well below attempts means people are
# skipping the question, not failing it.
#
# Unsubmitted (in-progress) attempts and the excluded system accounts are out.
MISSED=$(psql_ro "
  WITH att AS (
    SELECT DISTINCT ON (ea.user_id, ea.evaluation_id) ea.id, ea.evaluation_id
    FROM evaluation_attempt ea
    WHERE ea.submitted_at IS NOT NULL
      AND ea.user_id NOT IN ($EXCLUDE_SQL)
    ORDER BY ea.user_id, ea.evaluation_id, ea.submitted_at, ea.id
  ),
  tally AS (
    SELECT evaluation_id, COUNT(*)::int AS n_attempts FROM att GROUP BY evaluation_id
  ),
  graded AS (
    SELECT ans.question_id,
           CASE
             WHEN q.type = 'boolean'  AND sel.n_raw = 1 AND sel.ids[1] = ANY (cor.ids) THEN 1
             WHEN q.type = 'multiple' AND sel.n_raw > 0 AND sel.ids = cor.ids          THEN 1
             ELSE 0
           END AS correct
    FROM answer ans
    JOIN att ON att.id = ans.attempt_id
    JOIN question q ON q.id = ans.question_id
    LEFT JOIN LATERAL (
      SELECT COUNT(*)::int AS n_raw,
             COALESCE(ARRAY_AGG(DISTINCT v ORDER BY v), '{}'::text[]) AS ids
      FROM jsonb_array_elements_text(
             (CASE WHEN ans.selected_option_ids LIKE '[%]'
                   THEN ans.selected_option_ids END)::jsonb) AS t(v)
    ) sel ON TRUE
    LEFT JOIN LATERAL (
      SELECT COALESCE(ARRAY_AGG(DISTINCT o.id::text ORDER BY o.id::text), '{}'::text[]) AS ids
      FROM question_option o WHERE o.question_id = q.id AND o.is_correct
    ) cor ON TRUE
  )
  SELECT c.codigo,
         ev.title,
         REPLACE(LEFT(q.text, 90), '|', '/'),
         t.n_attempts,
         COUNT(g.correct)::int,
         ROUND(100.0 * (t.n_attempts - COALESCE(SUM(g.correct), 0)) / t.n_attempts)::int
  FROM question q
  JOIN evaluation ev ON ev.id = q.evaluation_id
  JOIN curso_seccion cs ON cs.id = ev.section_id
  JOIN curso c ON c.codigo = cs.curso
  JOIN tally t ON t.evaluation_id = ev.id
  LEFT JOIN graded g ON g.question_id = q.id
  GROUP BY c.codigo, ev.title, q.id, q.text, t.n_attempts
  ORDER BY 6 DESC, t.n_attempts DESC, q.text;") || fail "missed-questions query"

# Cap the emailed table but never silently: the count below reports the whole set.
MISSED_TOP=25
N_MISSED=$(printf '%s\n' "$MISSED" | /usr/bin/grep -c . || true)

UNTOUCHED=$(printf '%s\n' "$MEMBERS" | awk -F'|' '$4=="never"{print $2" <"$1">"}')
N_MEMBERS=$(printf '%s\n' "$MEMBERS" | /usr/bin/grep -c . || true)
N_UNTOUCHED=$(printf '%s\n' "$UNTOUCHED" | /usr/bin/grep -c . || true)
TODAY=$(date +%Y-%m-%d)

# ---------------------------------------------------------------------------
# Presentation
#
# Two hard constraints, both learned the hard way:
#
# 1. EVERY BYTE EMITTED HERE IS ASCII. Named entities only, never a literal
#    multi-byte character. This document is emailed and is also read straight
#    off disk, and in neither case does it get to declare a charset it can rely
#    on: a mail client picks its own, and a plain static file server sends
#    "text/html" with no charset at all, so a UTF-8 em dash renders as the
#    mojibake "a-hat-euro-emdash". A raw em dash in the header did exactly that.
#    Use &mdash; &middot; &rsquo; and friends, or plain ASCII.
# 2. EMAIL-SAFE CSS ONLY. Inline styles on every element, tables for layout,
#    hex colours, a system font stack. No <style> block (Gmail strips it), no
#    flexbox, no grid, no web fonts, no external images.
# ---------------------------------------------------------------------------
# No quoted family names in this stack, deliberately. The value is interpolated
# into style='...' attributes, so a quoted family ('Segoe UI') closes the
# attribute early and silently discards every declaration after font-family --
# which is how the header band shipped white-on-black text that rendered black.
FONT="-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
INK="#1a1d21"; MUTED="#6b7280"; RULE="#e5e7eb"; ZEBRA="#fafafa"; ACCENT="#b8860b"
TH="padding:9px 12px;text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:$MUTED;border-bottom:2px solid $RULE"
TD="padding:9px 12px;border-bottom:1px solid $RULE;vertical-align:top"
H3="margin:34px 0 4px;font-family:$FONT;font-size:15px;color:$INK;border-left:3px solid $ACCENT;padding-left:9px"
NOTE="margin:8px 0 0;font-family:$FONT;font-size:12px;color:$MUTED;line-height:1.5"
TABLE="border-collapse:collapse;width:100%;font-family:$FONT;font-size:13px;color:$INK;margin-top:10px"

REPORT_HTML=$(mktemp)
trap 'rm -f "$REPORT_HTML"' EXIT
{
  echo "<div style=\"background:#f4f5f7;padding:24px 0;font-family:$FONT\">"
  echo "<table role='presentation' cellpadding='0' cellspacing='0' style='margin:0 auto;width:100%;max-width:780px'><tr><td>"
  echo "<div style='background:#ffffff;border:1px solid $RULE;border-radius:10px;overflow:hidden'>"

  # Header band
  echo "<div style='background:$INK;padding:20px 24px'>"
  echo "<div style='font-family:$FONT;font-size:17px;color:#ffffff;font-weight:600'>Intent Solutions Learn</div>"
  echo "<div style='font-family:$FONT;font-size:13px;color:#9ca3af;margin-top:3px'>Member progress digest &middot; $TODAY</div>"
  echo "</div>"

  # Summary strip
  echo "<div style='padding:14px 24px;background:$ZEBRA;border-bottom:1px solid $RULE;font-family:$FONT;font-size:13px;color:$INK'>"
  echo "<b>$N_MEMBERS</b> active members &middot; <b>$N_UNTOUCHED</b> have not logged in yet"
  [ "$N_MISSED" -gt 0 ] && echo " &middot; <b>$N_MISSED</b> questions with attempt data"
  echo "</div>"

  echo "<div style='padding:4px 24px 24px'>"

  echo "<h3 style=\"$H3\">Members</h3>"
  echo "<table style=\"$TABLE\">"
  echo "<tr><th style=\"$TH\">Member</th><th style=\"$TH\">Role</th><th style=\"$TH\">Last access</th><th style=\"$TH;text-align:right\">Courses</th></tr>"
  [ -n "$MEMBERS" ] && printf '%s\n' "$MEMBERS" | awk -F'|' -v td="$TD" -v muted="$MUTED" -v zebra="$ZEBRA" '
    function esc(s){gsub(/&/,"\\&amp;",s);gsub(/</,"\\&lt;",s);gsub(/>/,"\\&gt;",s);gsub(/"/,"\\&quot;",s);gsub(/'\''/,"\\&#39;",s);return s}
    {bg=(NR%2==0)?"background:" zebra ";":"";
     last=($4=="never")?"<span style=\"color:#b45309\">never</span>":$4;
     printf "<tr style=\"%s\"><td style=\"%s\">%s<div style=\"color:%s;font-size:11px\">%s</div></td><td style=\"%s\">%s</td><td style=\"%s\">%s</td><td style=\"%s;text-align:right\">%s</td></tr>\n",
       bg,td,esc($2),muted,esc($1),td,esc($3),td,last,td,$5}'
  echo "</table>"

  echo "<h3 style=\"$H3\">Per-course progress</h3>"
  if [ -n "$PROGRESS" ]; then
    echo "<table style=\"$TABLE\">"
    echo "<tr><th style=\"$TH\">Member</th><th style=\"$TH\">Course</th><th style=\"$TH\">Progress</th><th style=\"$TH;text-align:right\">Done</th><th style=\"$TH\">Complete</th></tr>"
    printf '%s\n' "$PROGRESS" | awk -F'|' -v td="$TD" -v rule="$RULE" -v zebra="$ZEBRA" '
      function esc(s){gsub(/&/,"\\&amp;",s);gsub(/</,"\\&lt;",s);gsub(/>/,"\\&gt;",s);gsub(/"/,"\\&quot;",s);gsub(/'\''/,"\\&#39;",s);return s}
      {bg=(NR%2==0)?"background:" zebra ";":""; pct=$5+0; w=(pct<2&&pct>0)?2:pct;
       bar="<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" style=\"width:120px;background:" rule ";border-radius:3px\"><tr><td style=\"height:7px;width:" w "%;background:#2f6f4e;border-radius:3px;font-size:0;line-height:0\">&nbsp;</td><td style=\"font-size:0;line-height:0\">&nbsp;</td></tr></table>";
       done=($6=="t")?"yes":"no";
       printf "<tr style=\"%s\"><td style=\"%s\">%s</td><td style=\"%s\">%s</td><td style=\"%s\">%s<div style=\"font-size:11px;color:#6b7280;margin-top:2px\">%s%%</div></td><td style=\"%s;text-align:right\">%s/%s</td><td style=\"%s\">%s</td></tr>\n",
         bg,td,esc($1),td,esc($2),td,bar,pct,td,$3,$4,td,done}'
    echo "</table>"
  else
    echo "<p style=\"$NOTE\">No course activity recorded yet.</p>"
  fi

  echo "<h3 style=\"$H3\">Most-missed questions</h3>"
  if [ "$N_MISSED" -gt 0 ]; then
    if [ "$N_MISSED" -gt "$MISSED_TOP" ]; then
      echo "<p style=\"$NOTE\">Top $MISSED_TOP of $N_MISSED questions that have at least one submitted attempt, ranked by miss rate.</p>"
    else
      echo "<p style=\"$NOTE\">All $N_MISSED questions that have at least one submitted attempt, ranked by miss rate.</p>"
    fi
    echo "<table style=\"$TABLE\">"
    echo "<tr><th style=\"$TH;text-align:right\">Miss</th><th style=\"$TH\">Question</th><th style=\"$TH\">Course / evaluation</th><th style=\"$TH;text-align:right\">Answered</th></tr>"
    # Cap inside awk, never with `head`. Under `set -o pipefail` a `head` that stops
    # early closes the pipe, `printf` dies of SIGPIPE, the pipeline inherits that
    # non-zero status and `set -e` kills the whole script — so the digest would fail
    # to send precisely when there are MORE than MISSED_TOP rows, which is exactly
    # when it is worth sending. Found by Greptile on PR #81.
    printf '%s\n' "$MISSED" | awk -F'|' -v top="$MISSED_TOP" -v td="$TD" -v muted="$MUTED" -v zebra="$ZEBRA" '
      function esc(s){gsub(/&/,"\\&amp;",s);gsub(/</,"\\&lt;",s);gsub(/>/,"\\&gt;",s);gsub(/"/,"\\&quot;",s);gsub(/'\''/,"\\&#39;",s);return s}
      NR>top{next}
      {bg=(NR%2==0)?"background:" zebra ";":""; m=$6+0;
       col=(m>=70)?"#b91c1c":((m>=40)?"#b45309":"#4b5563");
       skip=($5<$4)?"<div style=\"font-size:11px;color:#b45309;margin-top:2px\">" ($4-$5) " skipped</div>":"";
       printf "<tr style=\"%s\"><td style=\"%s;text-align:right\"><span style=\"font-size:16px;font-weight:600;color:%s\">%s%%</span></td><td style=\"%s\">%s</td><td style=\"%s;color:%s;font-size:12px\">%s<div>%s</div></td><td style=\"%s;text-align:right\">%s/%s%s</td></tr>\n",
         bg,td,col,m,td,esc($3),td,muted,esc($1),esc($2),td,$5,$4,skip}'
    echo "</table>"
    echo "<p style=\"$NOTE\">Miss rate counts a skipped question as missed, matching how the platform scores an attempt. A skipped count means the question is being avoided rather than failed. Unsubmitted attempts and system accounts are excluded.</p>"
  else
    echo "<p style=\"$NOTE\">No submitted evaluation attempts yet.</p>"
  fi

  echo "<h3 style=\"$H3\">Certificates issued</h3>"
  if [ -n "$CERTS" ]; then
    echo "<table style=\"$TABLE\">"
    echo "<tr><th style=\"$TH\">Member</th><th style=\"$TH\">Course</th><th style=\"$TH\">Date</th></tr>"
    printf '%s\n' "$CERTS" | awk -F'|' -v td="$TD" -v zebra="$ZEBRA" '
      function esc(s){gsub(/&/,"\\&amp;",s);gsub(/</,"\\&lt;",s);gsub(/>/,"\\&gt;",s);gsub(/"/,"\\&quot;",s);gsub(/'\''/,"\\&#39;",s);return s}
      {bg=(NR%2==0)?"background:" zebra ";":"";
       printf "<tr style=\"%s\"><td style=\"%s\">%s</td><td style=\"%s\">%s</td><td style=\"%s\">%s</td></tr>\n",bg,td,esc($1),td,esc($2),td,esc($3)}'
    echo "</table>"
  else
    echo "<p style=\"$NOTE\">None yet.</p>"
  fi

  if [ -n "$UNTOUCHED" ]; then
    echo "<h3 style=\"$H3\">Not logged in yet (nudge list)</h3>"
    echo "<div style='font-family:$FONT;font-size:13px;color:$INK;line-height:1.9;margin-top:8px'>"
    printf '%s\n' "$UNTOUCHED" | sed 's/&/\&amp;/g;s/</\&lt;/g;s/>/\&gt;/g' \
      | sed "s|^|<div style='padding:6px 10px;background:#fff7ed;border-left:3px solid #f59e0b;margin-bottom:4px'>|;s|\$|</div>|"
    echo "</div>"
  fi

  echo "</div>"  # padded body
  echo "<div style='padding:14px 24px;background:$ZEBRA;border-top:1px solid $RULE;font-family:$FONT;font-size:11px;color:$MUTED;line-height:1.6'>"
  echo "Generated by <code>ops/lms/lms-progress-digest.sh</code>, read-only and server-enforced. Live detail: <a href='https://learn.intentsolutions.io' style='color:$ACCENT'>learn.intentsolutions.io</a>"
  echo "</div>"
  echo "</div></td></tr></table></div>"
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
