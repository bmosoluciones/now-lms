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
PATCH = "3"

# <--------------------------------------------------------------------------> #
# Quick fix
POST = ""

# <--------------------------------------------------------------------------> #
# Pre release not for production
PRERELEASE = ""

# <--------------------------------------------------------------------------> #
# Date of release
REVISION = ""

# <--------------------------------------------------------------------------> #
# Release string preprocessing
PRE_RELEASE_PART = (PRERELEASE if PRERELEASE != "" else "") + (REVISION if REVISION != "" else "")
POST_RELEASE_PART = (POST if POST != "" else "") + (REVISION if REVISION != "" else "")

# <--------------------------------------------------------------------------> #
# Release string
# Refences:
#  - https://peps.python.org/pep-0440/
#

BASE_VERSION = MAYOR + "." + MENOR + "." + PATCH

if PRERELEASE != "":
    VERSION = BASE_VERSION + PRE_RELEASE_PART

if POST != "":
    VERSION = BASE_VERSION + POST_RELEASE_PART

if PRERELEASE == "" and POST == "":
    VERSION = BASE_VERSION
