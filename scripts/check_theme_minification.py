#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Check that each theme's ``theme.min.css`` really is its ``theme.css``, minified.

WHY THIS EXISTS (bead now-lms-7g4)
Every bundled theme ships two hand-maintained copies of the same stylesheet, and
``local_style.j2`` loads the ``.min`` one. So the ``.css`` file is the one people
read and edit, and the ``.min.css`` file is the one users actually get. Nothing
checked that they agreed.

They do not. Measured 2026-07-31 on ``deploy/now-lms-fixed``, 7 of 8 themes have
drifted. ``corporative`` is the clearest case: after normalisation its ``.min``
is LARGER than its source, so the served stylesheet contains rules the source
does not have. Editing ``theme.css`` there changes nothing a user sees, silently.

HOW IT COMPARES
Not byte-for-byte -- that would just re-implement a minifier and fail on
whitespace. Both files are normalised (comments stripped, whitespace collapsed,
space around punctuation removed) and the resulting token streams compared. Two
files that differ only in formatting normalise to the same string; two files
that differ in a declaration do not.

That is deliberately a weaker claim than "this is the output of minifier X", and
a strong enough one to catch the failure that matters: an edit landing in one
copy and not the other.

SCOPE
Themes listed in GATED are blocking. Everything else is reported and does not
fail the run -- the 7 drifted themes are upstream-owned and predate this check,
and reddening the deploy line on inherited drift would just get the check turned
off. Move a theme into GATED once its two copies agree.

Usage:
    python scripts/check_theme_minification.py            # gate GATED, report the rest
    python scripts/check_theme_minification.py --all      # gate every theme
    python scripts/check_theme_minification.py --list     # report only, always exit 0
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Themes whose two copies are known to agree and must stay that way. Everything
# else is reported but not gated -- see SCOPE above.
# One entry today, deliberately: intent_learn is the only theme this fork owns,
# and the only one whose two copies currently agree. The other seven are
# upstream's and have already drifted -- see SCOPE. Add to this tuple only after
# `--all` passes for that theme, never to make a red run green.
GATED = ("intent_learn",)

THEMES_DIR = Path(__file__).resolve().parent.parent / "now_lms" / "static" / "themes"


def normalise(css: str) -> str:
    """Reduce a stylesheet to a formatting-insensitive token stream."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)  # comments
    css = re.sub(r"\s+", " ", css)  # runs of whitespace
    # Known limitation: `=` inside attribute selectors is not in this set, so
    # `[attr = v]` and `[attr=v]` normalise differently. Harmless — both files go
    # through the same function, so the comparison stays symmetric and this can
    # only ever cause a false ALARM on a real formatting difference, never a
    # missed drift. Left narrow rather than growing into a CSS parser.
    css = re.sub(r"\s*([{};:,>~+])\s*", r"\1", css)  # space around punctuation
    css = re.sub(r";}", "}", css)  # optional trailing semicolon
    return css.strip()


def check_theme(directory: Path) -> tuple[str, str]:
    """Return (status, detail) for one theme directory."""
    source, minified = directory / "theme.css", directory / "theme.min.css"
    if not source.exists() and not minified.exists():
        # For a GATED theme this is not "nothing to check" — it means the theme
        # ships no stylesheet at all while local_style.j2 still references one.
        # Ungated themes may legitimately have none, so the caller decides.
        return ("no-stylesheet", "theme has no theme.css and no theme.min.css")
    if not minified.exists():
        # A gated theme losing its .min is a FAILURE: local_style.j2 still
        # requests theme.min.css, so the deployed page 404s that request and
        # renders unstyled. This branch USED to return "skip", which let exactly
        # that pass green (Greptile P1, PR #61). Ungated themes still only report,
        # per SCOPE — the distinct status is what lets the caller decide.
        return ("missing-min", "theme.min.css is gone but local_style.j2 still requests it")
    if not source.exists():
        return ("fail", "theme.min.css exists with no theme.css to derive it from")

    normalised_source = normalise(source.read_text(encoding="utf-8"))
    normalised_min = normalise(minified.read_text(encoding="utf-8"))
    if normalised_source == normalised_min:
        return ("ok", "min matches source")

    delta = len(normalised_min) - len(normalised_source)
    if delta > 0:
        detail = f"min has {delta} chars MORE than source — the served file carries rules the source lacks"
    else:
        detail = f"min has {-delta} chars fewer than source — edits to theme.css are not reaching users"
    return ("fail", detail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="gate every theme, not just GATED")
    parser.add_argument("--list", action="store_true", help="report only; always exit 0")
    args = parser.parse_args()

    # argparse accepts both, and --list would silently win — so someone asking for
    # the strictest check (--all) alongside --list gets a guaranteed pass. Refuse
    # instead of picking one, because either guess makes the exit code a lie.
    if args.all and args.list:
        parser.error("--all and --list are mutually exclusive: one gates, the other never fails")

    # THEMES_DIR is derived from __file__, so moving this script silently points
    # it elsewhere. Fail loudly instead of reporting "gated themes OK" over an
    # empty or wrong directory (Kilo, PR #61).
    if not THEMES_DIR.is_dir():
        print(f"no themes directory at {THEMES_DIR}", file=sys.stderr)
        return 1
    missing_gated = [name for name in GATED if not (THEMES_DIR / name).is_dir()]
    if missing_gated:
        print(f"gated theme(s) not found under {THEMES_DIR}: {', '.join(missing_gated)}", file=sys.stderr)
        print("Either the theme was removed or this script has moved; refusing to report a pass.", file=sys.stderr)
        return 1

    blocking_failures = []
    reported = []

    for directory in sorted(p for p in THEMES_DIR.iterdir() if p.is_dir()):
        status, detail = check_theme(directory)
        gated = args.all or directory.name in GATED
        if status == "ok":
            print(f"  ok      {directory.name:14} {detail}")
        elif status == "skip":
            print(f"  skip    {directory.name:14} {detail}")
        elif status == "no-stylesheet" and not gated:
            print(f"  skip    {directory.name:14} {detail}  (not gated)")
        elif status == "missing-min" and not gated:
            print(f"  note    {directory.name:14} {detail}  (not gated)")
        elif gated:
            print(f"  FAIL    {directory.name:14} {detail}")
            blocking_failures.append(directory.name)
        else:
            print(f"  drift   {directory.name:14} {detail}  (not gated)")
            reported.append(directory.name)

    print()
    if reported:
        # Never let a bounded check read as full coverage.
        print(f"{len(reported)} theme(s) drifted but are NOT gated: {', '.join(reported)}")
        print("These are upstream-owned and predate this check (bead now-lms-7g4).")
        print("Run with --all to gate them once they are fixed.")
    if blocking_failures:
        print()
        print(f"FAILED: {', '.join(blocking_failures)}")
        print("theme.min.css must be regenerated from theme.css, or the edit applied to both.")
        return 0 if args.list else 1

    print("gated themes OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
