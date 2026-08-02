# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Auto-compile .po -> .mo if any .po is newer than its .mo.

ROOT CAUSE: .mo files are .gitignore'd (Babel convention), so any checkout
or pull leaves them at whatever state they were last compiled at. The
Dockerfile build step and CI run 'pybabel compile', but a developer who
clones fresh, a hot-reload demo instance, or any deploy that skipped the
image rebuild ships a stale .mo. Babel then falls back to the msgid
(Spanish literal) for every msgid that was added to .po after the .mo
was last compiled.

This helper is the root-cause fix: run at app boot (both wsgi.py and
run.py) so the catalog is always live before the first request is served.
The check is mtime-based and fast; if the .mo is already fresh, the
subprocess call is skipped.

This helper is intentionally idempotent and self-contained: it does not
import Flask or any application code, so it can be called before the
app is constructed (e.g. inside run.py BEFORE 'from now_lms import').
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_LOG = logging.getLogger("now_lms.i18n")
# Threshold for "is the .mo really stale?": if any .po is strictly newer
# than its .mo, recompile. Equal mtimes (or .mo newer than .po) are no-ops.
_STALE_MTIME_TOLERANCE_SECONDS = 1.0

# Sentinel msgids the --check gate proves are resolvable in each locale's
# compiled catalog. A stale .mo makes Babel fall back to the msgid (Spanish),
# which is the user-visible symptom this module exists to prevent.
#
# Keep one entry per user-visible surface. A locale absent from this map is
# compiled but not sentinel-checked, so add new locales here as they land.
# Only msgids that actually exist in the .po files belong here: a msgid that
# was never extracted falls back to Spanish regardless of .mo freshness, and
# gating on it would make the check fail for a reason it cannot fix.
_CATALOG_SENTINELS: dict[str, dict[str, str]] = {
    "en": {"Genero": "Gender", "Título": "Qualification"},
    "pt_BR": {"Genero": "Gênero", "Título": "Qualificação"},
}


def _find_pybabel() -> str | None:
    """Return the pybabel executable name, or None if Babel is not installed.

    pybabel is a console script installed by Babel; on Windows the entry
    point can be named pybabel-script.py. Returning None is not fatal - the
    caller logs the manual compile command and leaves the catalog alone.
    """
    from shutil import which

    for candidate in ("pybabel", "pybabel-script.py"):
        if which(candidate):
            return candidate
    return None


def _catalog_root() -> Path:
    """Locate now_lms/translations, relative to this module."""
    # i18n.py lives at now_lms/i18n.py; translations/ is its sibling.
    return Path(__file__).resolve().parent / "translations"


def _is_stale(po_path: Path, mo_path: Path) -> bool:
    if not mo_path.exists():
        return True
    po_mtime = po_path.stat().st_mtime
    mo_mtime = mo_path.stat().st_mtime
    return (po_mtime - mo_mtime) > _STALE_MTIME_TOLERANCE_SECONDS


def ensure_translations_compiled(force: bool = False) -> bool:
    """Recompile .po -> .mo if any locale catalog is stale.

    Args:
        force: If True, recompile unconditionally. Used by CI/dev/test.sh
            to keep the gate deterministic.

    Returns:
        True if a recompile happened, False if the .mo files were already
        fresh. Failures are logged but never raise: a broken Babel install
        must not stop the app from booting. The build-time gate
        (``--check``) is what refuses to ship a stale catalog.
    """
    root = _catalog_root()
    if not root.exists():
        _LOG.warning("i18n: translations directory not found at %s", root)
        return False

    pybabel = _find_pybabel()
    if pybabel is None:
        _LOG.warning(
            "i18n: pybabel not on PATH; cannot auto-compile stale .mo. "
            "Install Babel (pip install babel==2.18.0) or run "
            "'pybabel compile -d %s' manually before starting the app.",
            root,
        )
        return False

    if not _stale_catalogs(root, force):
        return False

    # Serialise across processes. WSGI servers boot N workers at once and every
    # one of them would otherwise run pybabel against the same .mo files
    # concurrently, which can leave a half-written catalog on disk - a worse
    # failure than the stale one being fixed. The lock is best-effort: if it
    # cannot be taken (read-only install dir, no fcntl) we compile anyway,
    # which is the pre-existing behaviour.
    with _compile_lock(root):
        # Re-check under the lock: whoever held it first may have done the work.
        stale = _stale_catalogs(root, force)
        if not stale:
            _LOG.info("i18n: catalog refreshed by another worker - nothing to do")
            return False
        return _run_pybabel(pybabel, root, stale, force)


def _stale_catalogs(root: Path, force: bool) -> list[Path]:
    """Return the .po files whose .mo is missing or older than they are."""
    return [po for po in sorted(root.glob("*/LC_MESSAGES/messages.po")) if force or _is_stale(po, po.with_suffix(".mo"))]


@contextmanager
def _compile_lock(root: Path) -> Iterator[None]:
    """Hold an advisory lock while compiling, if the platform and FS allow it."""
    try:
        import fcntl
    except ImportError:  # pragma: no cover - non-POSIX
        yield
        return
    try:
        handle = open(root / ".compile.lock", "w", encoding="utf-8")  # noqa: SIM115
    except OSError as exc:
        _LOG.debug("i18n: cannot create compile lock (%s); compiling unlocked", exc)
        yield
        return
    try:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield
    finally:
        handle.close()


def _run_pybabel(pybabel: str, root: Path, stale: list[Path], force: bool) -> bool:
    """Compile the catalogs. Returns True on success, False on any failure."""
    _LOG.info(
        "i18n: %d catalog(s) stale (.po newer than .mo) - auto-compiling",
        len(stale),
    )
    try:
        cmd = [str(pybabel), "compile", "-d", str(root)]
        if force:
            cmd.append("-f")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        if result.returncode != 0:
            _LOG.error(
                "i18n: pybabel compile failed (rc=%d):\nstdout=%s\nstderr=%s",
                result.returncode,
                result.stdout,
                result.stderr,
            )
            return False
        _LOG.info("i18n: catalog recompiled - %d locale(s)", len(stale))
        return True
    except OSError as exc:
        _LOG.error("i18n: pybabel spawn failed: %s", exc)
        return False


def stale_catalog_locales() -> list[str]:
    """Return the list of locale codes whose .po is newer than their .mo.

    Read-only; used by the tests and available for operator diagnostics.
    """
    root = _catalog_root()
    out = []
    for po in sorted(root.glob("*/LC_MESSAGES/messages.po")):
        locale = po.parts[-3]
        mo = po.with_suffix(".mo")
        if _is_stale(po, mo):
            out.append(locale)
    return out


# Runs in a clean interpreter (see _probe_freshness_in_subprocess). Takes the
# .mo path and a JSON {msgid: expected_msgstr} map as argv; exits 1 with a
# one-line reason on any problem so the caller can surface it verbatim.
_PROBE_SCRIPT = """\
import json, sys
from io import BytesIO

path, expected = sys.argv[1], json.loads(sys.argv[2])
try:
    from babel.messages.mofile import read_mo
    try:
        with open(path, 'rb') as handle:
            buf = handle.read()
    except FileNotFoundError:
        sys.exit('i18n_autocompile: %s missing' % path)
    if len(buf) < 20:
        sys.exit('i18n_autocompile: %s header too short' % path)
    if buf[:4] not in (b'\\xde\\x12\\x04\\x95', b'\\x95\\x04\\x12\\xde'):
        sys.exit('i18n_autocompile: %s bad magic' % path)
    catalog = read_mo(BytesIO(buf))
    missing = [
        msgid for msgid, msgstr in expected.items()
        if catalog.get(msgid) is None or catalog.get(msgid).string != msgstr
    ]
    if missing:
        sys.exit('i18n_autocompile: %s stale, unresolved msgids: %r' % (path, missing))
except Exception as exc:  # noqa: BLE001 - report, never traceback
    sys.exit('i18n_autocompile: probe crashed on %s: %s' % (path, exc))
"""


def _probe_freshness_in_subprocess(locale: str) -> bool:
    """Spawn a fresh Python to probe the .mo from scratch.

    Babel caches translations at module-import time, so an in-process
    probe returns stale data even after the .mo on disk is fresh. We
    need a clean subprocess so the catalog is reloaded.

    Probe directly via babel.messages.mofile (no Flask-Babel config
    dance) so the result is unambiguous. Any failure (corrupt file,
    malformed header, missing msgids) exits 1 cleanly.
    """
    mo_path = _catalog_root() / locale / "LC_MESSAGES" / "messages.mo"
    expected = _CATALOG_SENTINELS.get(locale, {})
    try:
        result = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT, str(mo_path), json.dumps(expected)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return True
        if result.stderr:
            sys.stderr.write(result.stderr)
        return False
    except (OSError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write("i18n_autocompile: probe subprocess failed: " + str(exc) + chr(10))
        return False


def _main() -> int:
    """CLI entry point: `python -m now_lms.i18n_autocompile [--check] [--force]`.

    Without flags: recompile stale catalogs (silent no-op if fresh).
    --check: exit 0 if all sentinels translate, exit 1 otherwise. Used by CI.
    --force: recompile unconditionally. Used by dev/catalog_freshness_check.sh.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="python -m now_lms.i18n_autocompile")
    parser.add_argument("--check", action="store_true", help="Verify every locale's .mo resolves the sentinel msgids.")
    parser.add_argument("--force", action="store_true", help="Recompile all catalogs unconditionally.")
    parser.add_argument("--locale", default=None, help="Locale to check (default: every locale with a .po).")
    args = parser.parse_args()

    if args.force:
        ensure_translations_compiled(force=True)
        return 0

    if args.check:
        ensure_translations_compiled(force=False)
        locales = (
            [args.locale]
            if args.locale
            else [po.parts[-3] for po in sorted(_catalog_root().glob("*/LC_MESSAGES/messages.po"))]
        )
        all_ok = True
        for locale in locales:
            if not _probe_freshness_in_subprocess(locale):
                print(f"i18n_autocompile --check: locale={locale} FAIL (stale or missing)")
                all_ok = False
            else:
                print(f"i18n_autocompile --check: locale={locale} OK")
        return 0 if all_ok else 1

    changed = ensure_translations_compiled(force=False)
    print(f"i18n_autocompile: {'recompiled' if changed else 'no-op'}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
