# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Definición unica de la version de la aplicación."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------

# <--------------------------------------------------------------------------> #
# Basic info:
APPNAME = "NOW lms"
APPAUTHOR = "BMO Soluciones, S.A."

# <--------------------------------------------------------------------------> #
CODE_NAME = "Karla"

# <--------------------------------------------------------------------------> #
# SemVer (https://semver.org)
MAYOR = "1"
MENOR = "3"
PATCH = "2"

# <--------------------------------------------------------------------------> #
# Quick fix
POST = os.environ.get("NOW_LMS_VERSION_POST")

# <--------------------------------------------------------------------------> #
# Pre release not for production
PRERELEASE = os.environ.get("NOW_LMS_VERSION_PRERELEASE")

# <--------------------------------------------------------------------------> #
# Date of release
REVISION = os.environ.get("NOW_LMS_VERSION_REVISION")

# <--------------------------------------------------------------------------> #
# Release string
# References:
#  - https://peps.python.org/pep-0440/
#  - https://semver.org/
#
# Formula: {MAYOR}.{MENOR}.{PATCH}[{PRERELEASE}][.{POST}[.{REVISION}]]
#   Examples:
#     1.3.0              -> stable release
#     1.3.0a1            -> alpha pre-release
#     1.3.0b2            -> beta pre-release
#     1.3.0rc1           -> release candidate
#     1.3.0.post1        -> post-release
#     1.3.0.post1.202601 -> post-release with revision date
#

BASE_VERSION = f"{MAYOR}.{MENOR}.{PATCH}"

if PRERELEASE:
    VERSION = f"{BASE_VERSION}{PRERELEASE}"
elif POST:
    revision_part = f".{REVISION}" if REVISION else ""
    VERSION = f"{BASE_VERSION}.post{POST}{revision_part}"
else:
    VERSION = BASE_VERSION
