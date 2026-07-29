# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Every translatable string must actually be extractable.

``_l`` (``lazy_gettext``) is not one of Babel's default keywords, so an
extraction run without ``-k _l`` silently skips every lazily-translated form
label — they render in the source language forever, with no msgid for a
translator to fill in. This test runs the real extraction and asserts the
lazily-labelled strings come out.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LANG_SCRIPT = REPO_ROOT / "dev" / "lang.sh"


def _extract(tmp_path: Path, *extra_args: str) -> str:
    pot = tmp_path / "messages.pot"
    result = subprocess.run(
        [sys.executable, "-m", "babel.messages.frontend", "extract", "-F", "babel.cfg", *extra_args, "-o", str(pot), "."],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:  # pragma: no cover - surfaced only on a broken toolchain
        pytest.skip(f"pybabel extract unavailable: {result.stderr[-300:]}")
    return pot.read_text(encoding="utf-8")


@pytest.mark.slow
def test_lazy_labels_are_extractable(tmp_path):
    """A label that exists only as _l() must appear in the extracted catalogue."""
    catalogue = _extract(tmp_path, "-k", "_l")
    # "URL de Facebook" is a ConfigForm label and appears nowhere else in the
    # source, so it is a clean probe for _l extraction.
    assert 'msgid "URL de Facebook"' in catalogue


def test_lang_script_passes_the_lazy_keyword():
    """dev/lang.sh must keep -k _l, or lazy labels silently stop being extracted."""
    script = LANG_SCRIPT.read_text(encoding="utf-8")
    extract_line = next(line for line in script.splitlines() if line.startswith("pybabel extract"))
    assert re.search(r"-k\s+_l\b", extract_line), (
        "dev/lang.sh must pass -k _l to pybabel extract; without it every _l() form label is skipped"
    )


def test_lang_script_passes_the_plural_keyword():
    """Same for -k _n:1,2, so the documented plural helper is extractable."""
    script = LANG_SCRIPT.read_text(encoding="utf-8")
    extract_line = next(line for line in script.splitlines() if line.startswith("pybabel extract"))
    assert re.search(r"-k\s+_n:1,2\b", extract_line), (
        "dev/lang.sh must pass -k _n:1,2 to pybabel extract; without it every _n() plural is skipped"
    )


@pytest.mark.slow
def test_plural_helper_is_extractable_with_the_declared_keyword(tmp_path):
    """Prove the keyword spec works, without adding an unused _n() call to the app.

    Extracts from a throwaway module that calls _n(), first with Babel's defaults
    and then with the spec dev/lang.sh now declares.
    """
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    (probe_dir / "probe.py").write_text(
        "from now_lms.i18n import _n\n\n\ndef describe(count):\n"
        '    return _n("%(num)d archivo pendiente", "%(num)d archivos pendientes", count, num=count)\n',
        encoding="utf-8",
    )
    (probe_dir / "babel.cfg").write_text("[python: **.py]\n", encoding="utf-8")

    def extract(*extra: str) -> str:
        pot = tmp_path / f"probe{len(extra)}.pot"
        result = subprocess.run(
            [sys.executable, "-m", "babel.messages.frontend", "extract", "-F", "babel.cfg", *extra, "-o", str(pot), "."],
            cwd=probe_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:  # pragma: no cover - broken toolchain only
            pytest.skip(f"pybabel extract unavailable: {result.stderr[-300:]}")
        return pot.read_text(encoding="utf-8")

    assert 'msgid "%(num)d archivo pendiente"' not in extract(), "expected Babel defaults to miss _n()"
    assert 'msgid "%(num)d archivo pendiente"' in extract("-k", "_n:1,2"), "-k _n:1,2 should pick up the singular"
    assert 'msgid_plural "%(num)d archivos pendientes"' in extract("-k", "_n:1,2"), "and the plural form"
