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
