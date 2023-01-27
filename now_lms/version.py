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

from datetime import datetime


APPNAME = "NOW lms"
APPAUTHOR = "BMO Soluciones, S.A."
MAYOR = "0"
MENOR = "0"
PATCH = "1"
REVISION = datetime.today().strftime("%Y%m%d")
PRERELEASE = "alpha-1"
if PRERELEASE:
    VERSION = MAYOR + "." + MENOR + "." + PATCH + "." + PRERELEASE + REVISION
else:
    VERSION = MAYOR + "." + MENOR + "." + PATCH + "." + REVISION
