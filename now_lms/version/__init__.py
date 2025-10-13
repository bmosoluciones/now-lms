# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
MENOR = "0"
PATCH = "0"

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
