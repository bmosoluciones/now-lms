#!/usr/bin/env python3
"""
Ensure company header is present at the top of Python source files.

- Checks Python files under selected paths (default: now_lms/, tests/).
- In --apply mode, prepends the header when missing, preserving shebang lines.

Usage:
  python dev/ensure_headers.py --check
  python dev/ensure_headers.py --apply
  python dev/ensure_headers.py --check --paths now_lms,vistas

Exit codes:
  0 - Success (all files have header or fixed in apply mode)
  1 - Missing headers found in check mode
  2 - Unexpected error
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable

HEADER = (
    "# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
# Copyright 2025 - 2026 BMO Soluciones, S.A.\n"
    "#\n"
    '# Licensed under the Apache License, Version 2.0 (the "License");\n'
    "# you may not use this file except in compliance with the License.\n"
    "# You may obtain a copy of the License at\n"
    "#\n"
    "#    http://www.apache.org/licenses/LICENSE-2.0\n"
    "#\n"
    "# Unless required by applicable law or agreed to in writing, software\n"
    '# distributed under the License is distributed on an "AS IS" BASIS,\n'
    "# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n"
    "# See the License for the specific language governing permissions and\n"
    "# limitations under the License.\n"
    "\n"
)

DEFAULT_PATHS = ["now_lms", "tests"]
SKIP_DIRS = {"__pycache__", "migrations", ".git", ".github", "node_modules", "venv"}


def iter_python_files(root_paths: Iterable[str]) -> Iterable[str]:
    for root in root_paths:
        if not os.path.exists(root):
            continue
        if os.path.isfile(root) and root.endswith(".py"):
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune skip dirs
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                if fname.endswith(".py"):
                    yield os.path.join(dirpath, fname)


def has_header(content: str) -> bool:
    return content.startswith(HEADER) or HEADER in content.splitlines(True)[:25]


def ensure_header_in_file(filepath: str, apply: bool) -> bool:
    """Returns True if header exists or was added. False if missing and not applied."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # skip non-utf8 files
        return True

    if has_header(content):
        return True

    if not apply:
        return False

    # Preserve shebang if present
    shebang = ""
    rest = content
    if content.startswith("#!"):
        first_newline = content.find("\n")
        if first_newline != -1:
            shebang = content[: first_newline + 1]
            rest = content[first_newline + 1 :]

    new_content = f"{shebang}{HEADER}{rest}"
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure company header in Python files")
    parser.add_argument("--check", action="store_true", help="Only check; fail if missing headers")
    parser.add_argument("--apply", action="store_true", help="Apply header to files missing it")
    parser.add_argument(
        "--paths",
        type=str,
        default=",".join(DEFAULT_PATHS),
        help="Comma-separated list of root paths to scan",
    )
    args = parser.parse_args()

    if not args.check and not args.apply:
        parser.print_help()
        return 2

    roots = [p.strip() for p in args.paths.split(",") if p.strip()]

    missing: list[str] = []
    for fpath in iter_python_files(roots):
        ok = ensure_header_in_file(fpath, apply=args.apply)
        if not ok:
            missing.append(fpath)

    if missing:
        print("Missing headers in:")
        for m in missing:
            print(f" - {m}")
        return 1 if args.check and not args.apply else 0

    print("All checked files have the company header.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
