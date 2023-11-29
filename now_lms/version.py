# Copyright 2022 -2023 BMO Soluciones, S.A.
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
# Contributors:
# - William José Moreno Reyes


"""Definición unica de la version de la aplicación."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------


# <--------------------------------------------------------------------------> #
# Basic info:
APPNAME = "NOW lms"
APPAUTHOR = "BMO Soluciones, S.A."

# <--------------------------------------------------------------------------> #
# SemVer (https://semver.org)
MAYOR = "0"
MENOR = "0"
PATCH = "1"

# <--------------------------------------------------------------------------> #
# Pre release data.
PRERELEASE = "a13"
REVISION = datetime.today().strftime("%Y%m%d")

# <--------------------------------------------------------------------------> #
# Release string
# Refences:
#  - https://peps.python.org/pep-0440/
# 0.0.1a13.dev20231129
if PRERELEASE:  # pragma: no cover
    VERSION = MAYOR + "." + MENOR + "." + PATCH + PRERELEASE + ".dev" + REVISION
else:  # pragma: no cover
    VERSION = MAYOR + "." + MENOR + "." + PATCH
