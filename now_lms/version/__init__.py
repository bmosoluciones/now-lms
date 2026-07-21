# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Definición unica de la version de la aplicación."""

from __future__ import annotations

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
MENOR = "2"
PATCH = "5"

# <--------------------------------------------------------------------------> #
# Quick fix
POST = None

# <--------------------------------------------------------------------------> #
# Pre release not for production
PRERELEASE = None

# <--------------------------------------------------------------------------> #
# Date of release
REVISION = None

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

BASE_VERSION = MAYOR + "." + MENOR + "." + PATCH

if PRERELEASE is not None:
    VERSION = BASE_VERSION + PRERELEASE
elif POST is not None:
    revision_part = "." + REVISION if REVISION is not None else ""
    VERSION = BASE_VERSION + ".post" + POST + revision_part
else:
    VERSION = BASE_VERSION
