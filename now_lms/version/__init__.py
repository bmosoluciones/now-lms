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
MAYOR = "0"
MENOR = "0"
PATCH = "1"

# <--------------------------------------------------------------------------> #
# Quick fix
POST = False

# <--------------------------------------------------------------------------> #
# Pre release not for production
PRERELEASE = "b12"

# <--------------------------------------------------------------------------> #
# Date of release
REVISION = "20250823"

# <--------------------------------------------------------------------------> #
# Release string
# Refences:
#  - https://peps.python.org/pep-0440/
# 0.0.1b12.dev20250823
if PRERELEASE:
    VERSION = MAYOR + "." + MENOR + "." + PATCH + PRERELEASE + ".dev" + REVISION
else:
    if not POST:
        VERSION = MAYOR + "." + MENOR + "." + PATCH
    else:
        VERSION = MAYOR + "." + MENOR + "." + PATCH + ".post" + REVISION
