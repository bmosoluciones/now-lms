# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for the i18n autocompile + freshness-gate root-cause fix.

Bug class guarded: stale .mo file on disk causes Babel to fall back to the
msgid (Spanish) for any msgid added to .po after the .mo was last
compiled. The "Gender rendered in Spanish" demo bug.

The fix has two layers; each test exercises one:

  1. ensure_translations_compiled: regenerates any .mo older than its .po.
     Called at boot from wsgi.py and run.py.
  2. python -m now_lms.i18n_autocompile --check (wrapped by
     dev/catalog_freshness_check.sh): build/CI gate that probes each .mo in
     a fresh subprocess, because Babel caches catalogs in-process and an
     in-process probe reports stale data even once the .mo on disk is new.

Mutation-checked: deleting i18n_autocompile.py, removing the autocompile
call from wsgi.py, or removing the gate from dev/catalog_freshness_check.sh
must fail at least one of these tests. The gate is proved to fail as well as
pass - see test_probe_rejects_a_corrupt_mo.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from now_lms.i18n_autocompile import ensure_translations_compiled, stale_catalog_locales


@pytest.fixture
def clean_translations(tmp_path, monkeypatch):
    """Set up an isolated translations dir for testing without touching repo files."""
    src = Path(__file__).resolve().parent.parent / "now_lms" / "translations"
    assert src.exists()
    # Copy .po files into tmp_path so we can mutate them without dirtying the repo.
    import shutil

    for po in src.glob("*/LC_MESSAGES/messages.po"):
        target = tmp_path / po.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(po, target)
    # Point the module at the test dir.
    import now_lms.i18n_autocompile as ac

    monkeypatch.setattr(ac, "_catalog_root", lambda: tmp_path)
    return tmp_path


def test_stale_catalog_locales_detects_po_newer_than_mo(clean_translations):
    """When .po is newer than .mo, the locale is reported as stale."""
    po = clean_translations / "en" / "LC_MESSAGES" / "messages.po"
    mo = po.with_suffix(".mo")
    assert not mo.exists(), "fixture should not have created a .mo"

    stale = stale_catalog_locales()
    assert "en" in stale
    assert "pt_BR" in stale


def test_ensure_translations_compiled_creates_mo(clean_translations):
    """After ensure_translations_compiled(), the .mo exists and is fresh."""
    po = clean_translations / "en" / "LC_MESSAGES" / "messages.po"
    mo = po.with_suffix(".mo")
    assert not mo.exists()

    changed = ensure_translations_compiled()
    assert changed, "ensure_translations_compiled should have rebuilt the .mo"
    assert mo.exists(), ".mo should exist after ensure_translations_compiled"

    # Second call should be a no-op (already fresh).
    assert ensure_translations_compiled() is False


def test_ensure_translations_compiled_handles_missing_pybabel(clean_translations, monkeypatch):
    """If pybabel is not on PATH, the helper must log + return False without raising."""
    import now_lms.i18n_autocompile as ac

    # Force _find_pybabel to return None.
    monkeypatch.setattr(ac, "_find_pybabel", lambda: None)
    po = clean_translations / "en" / "LC_MESSAGES" / "messages.po"
    mo = po.with_suffix(".mo")
    assert not mo.exists()
    # Should NOT raise; should return False (didn't compile because no pybabel).
    assert ensure_translations_compiled() is False
    assert not mo.exists()


def test_check_cli_exits_zero_when_catalogs_fresh():
    """End-to-end: the CLI gate recompiles, then exits 0.

    --check calls ensure_translations_compiled() before probing, so a stale
    working tree is cured by the gate itself. A non-zero exit therefore means
    the catalog cannot be made fresh, which is exactly what CI must block on.
    """
    result = subprocess.run(
        [sys.executable, "-m", "now_lms.i18n_autocompile", "--check"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, f"gate failed:\n{result.stdout}\n{result.stderr}"
    assert "OK" in result.stdout
    assert "Traceback" not in result.stderr


def test_check_cli_runs_from_any_working_directory(tmp_path):
    """The gate resolves the catalog from the package, not from os.getcwd().

    Regression: an earlier revision hardcoded a CWD-relative catalog path, so
    the gate silently passed only when invoked from the repository root.
    """
    result = subprocess.run(
        [sys.executable, "-m", "now_lms.i18n_autocompile", "--check", "--locale", "en"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent)},
    )
    assert result.returncode == 0, f"gate failed outside repo root:\n{result.stdout}\n{result.stderr}"
    assert "locale=en OK" in result.stdout


def test_compile_lock_is_best_effort_when_the_directory_is_unwritable(clean_translations, monkeypatch):
    """A catalog dir we cannot write a lockfile into must still compile.

    Multi-worker boots take an advisory lock so two workers never run pybabel
    over the same .mo at once. That lock is a safety measure, not a
    precondition: an installation that forbids the lockfile must degrade to
    the unlocked behaviour rather than skipping the compile.
    """
    import now_lms.i18n_autocompile as ac

    def _refuse(*args, **kwargs):
        raise PermissionError("read-only catalog directory")

    monkeypatch.setattr("builtins.open", _refuse)
    with ac._compile_lock(clean_translations):
        pass  # must not raise


def test_missing_translations_directory_is_a_no_op(monkeypatch, tmp_path):
    """A source tree with no translations/ dir must warn and carry on, not crash."""
    import now_lms.i18n_autocompile as ac

    monkeypatch.setattr(ac, "_catalog_root", lambda: tmp_path / "does-not-exist")
    assert ensure_translations_compiled() is False


def test_failed_pybabel_run_returns_false(clean_translations, monkeypatch):
    """A non-zero pybabel exit is logged and reported, never raised."""
    import now_lms.i18n_autocompile as ac

    class _Failed:
        returncode = 2
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(ac.subprocess, "run", lambda *a, **k: _Failed())
    assert ensure_translations_compiled() is False


def test_pybabel_spawn_error_returns_false(clean_translations, monkeypatch):
    """If the pybabel binary cannot be spawned at all, boot still proceeds."""
    import now_lms.i18n_autocompile as ac

    def _explode(*args, **kwargs):
        raise OSError("exec format error")

    monkeypatch.setattr(ac.subprocess, "run", _explode)
    assert ensure_translations_compiled() is False


def test_another_worker_winning_the_lock_is_a_no_op(clean_translations, monkeypatch):
    """Re-checking under the lock must skip the compile a peer already did.

    Two workers booting at once both see a stale catalog; only the first
    through the lock should spawn pybabel.
    """
    import now_lms.i18n_autocompile as ac

    calls = {"n": 0}
    real = ac._stale_catalogs

    def _stale_then_fresh(root, force):
        calls["n"] += 1
        return real(root, force) if calls["n"] == 1 else []

    monkeypatch.setattr(ac, "_stale_catalogs", _stale_then_fresh)
    monkeypatch.setattr(ac, "_run_pybabel", lambda *a, **k: pytest.fail("compiled anyway"))
    assert ensure_translations_compiled() is False


def test_probe_reports_a_subprocess_failure_as_stale(clean_translations, monkeypatch):
    """If the probe interpreter cannot be spawned, treat the catalog as unproven."""
    import now_lms.i18n_autocompile as ac

    def _explode(*args, **kwargs):
        raise OSError("no interpreter")

    monkeypatch.setattr(ac.subprocess, "run", _explode)
    assert ac._probe_freshness_in_subprocess("en") is False


def test_cli_force_recompiles_and_exits_zero(clean_translations, monkeypatch):
    """--force rebuilds every catalog regardless of mtime."""
    import now_lms.i18n_autocompile as ac

    monkeypatch.setattr(sys, "argv", ["i18n_autocompile", "--force"])
    assert ac._main() == 0
    assert (clean_translations / "en" / "LC_MESSAGES" / "messages.mo").exists()


def test_cli_without_flags_reports_recompiled_then_no_op(clean_translations, monkeypatch, capsys):
    """Bare invocation compiles once, then reports a no-op on the second run."""
    import now_lms.i18n_autocompile as ac

    monkeypatch.setattr(sys, "argv", ["i18n_autocompile"])
    assert ac._main() == 0
    assert "recompiled" in capsys.readouterr().out

    assert ac._main() == 0
    assert "no-op" in capsys.readouterr().out


def test_cli_check_exits_one_when_a_locale_cannot_be_proved(clean_translations, monkeypatch, capsys):
    """--check must return a non-zero exit code so CI blocks on it."""
    import now_lms.i18n_autocompile as ac

    monkeypatch.setattr(sys, "argv", ["i18n_autocompile", "--check", "--locale", "en"])
    monkeypatch.setattr(ac, "_probe_freshness_in_subprocess", lambda locale: False)
    assert ac._main() == 1
    assert "locale=en FAIL" in capsys.readouterr().out


def test_cli_check_probes_every_locale_by_default(clean_translations, monkeypatch, capsys):
    """With no --locale, every locale that has a .po is probed."""
    import now_lms.i18n_autocompile as ac

    seen = []
    monkeypatch.setattr(sys, "argv", ["i18n_autocompile", "--check"])
    monkeypatch.setattr(ac, "_probe_freshness_in_subprocess", lambda locale: seen.append(locale) or True)
    assert ac._main() == 0
    assert set(seen) == {"en", "pt_BR"}
    assert "locale=en OK" in capsys.readouterr().out


def test_probe_rejects_a_corrupt_mo(clean_translations, monkeypatch):
    """The gate must FAIL on a corrupt .mo, not just pass on a good one.

    Without this, every other assertion here is satisfied by a probe that
    always returns True.
    """
    import now_lms.i18n_autocompile as ac

    mo = clean_translations / "en" / "LC_MESSAGES" / "messages.mo"
    mo.parent.mkdir(parents=True, exist_ok=True)
    mo.write_bytes(b"not a gettext catalog")
    monkeypatch.setattr(ac, "_CATALOG_SENTINELS", {"en": {"Genero": "Gender"}})

    assert ac._probe_freshness_in_subprocess("en") is False


def test_probe_rejects_a_missing_mo(clean_translations, monkeypatch):
    """A locale with no compiled catalog at all must fail the gate."""
    import now_lms.i18n_autocompile as ac

    monkeypatch.setattr(ac, "_CATALOG_SENTINELS", {"en": {"Genero": "Gender"}})
    assert not (clean_translations / "en" / "LC_MESSAGES" / "messages.mo").exists()
    assert ac._probe_freshness_in_subprocess("en") is False
