#!/usr/bin/env bash
# Install the fork-local L1 lint gate into this clone's git hook chain.
#
# WHY A SHIM: this repo's core.hooksPath is .beads/hooks (set by `bd init`) so
# beads can sync its Dolt database on git events — that must keep working, and
# .beads/ is git-ignored, so the hook file itself cannot travel with the repo.
# The enforcement DOES travel: the gate is scripts/pre-commit-lint.sh (tracked);
# this installer appends a 4-line shim to .beads/hooks/pre-commit OUTSIDE the
# "BEGIN/END BEADS INTEGRATION" markers, which beads preserves when it manages
# its own section. Chosen over pointing core.hooksPath at a tracked hooks dir
# because that would orphan beads' other four hooks (post-checkout, post-merge,
# pre-push, prepare-commit-msg).
#
# Idempotent: run once per clone, after `bd init` / `bd hooks install`.
# Verify afterward: `bd hooks list` must still report all 5 beads hooks.
#
# Fork-local (Intent Solutions engineering standard); never offered upstream.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
hook="$root/.beads/hooks/pre-commit"
marker="# --- fork-local L1 lint gate (managed by scripts/install-git-hooks.sh) ---"

# bd writes hooksPath as either a relative or an absolute path — accept both.
hooks_path=$(git config core.hooksPath || true)
case "$hooks_path" in
    .beads/hooks | */.beads/hooks) ;;
    *)
        echo "warning: core.hooksPath is '$hooks_path', not .beads/hooks — run 'bd hooks install'" >&2
        echo "first, then re-run this script. Nothing installed." >&2
        exit 1
        ;;
esac

if [ ! -f "$hook" ]; then
    echo "error: $hook not found — run 'bd init' or 'bd hooks install' first." >&2
    exit 1
fi

if grep -qF "$marker" "$hook"; then
    echo "already installed: L1 shim present in .beads/hooks/pre-commit"
    exit 0
fi

cat >>"$hook" <<EOF

$marker
# The gate itself is tracked at scripts/pre-commit-lint.sh; this shim is
# per-clone because .beads/hooks is git-ignored. Do not edit the beads-managed
# section above; re-run scripts/install-git-hooks.sh if this block goes missing.
_repo_root=\$(git rev-parse --show-toplevel 2>/dev/null)
if [ -n "\$_repo_root" ] && [ -x "\$_repo_root/scripts/pre-commit-lint.sh" ]; then
  "\$_repo_root/scripts/pre-commit-lint.sh" || exit \$?
fi
EOF

chmod +x "$hook"
echo "installed: L1 shim appended to .beads/hooks/pre-commit (outside beads markers)"
