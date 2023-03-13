# Copyright 2022 - 2023 BMO Soluciones, S.A.
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

"""NOW-LMS setup."""

from os import path
from setuptools import setup


aqui = path.abspath(path.dirname(__file__))
with open(path.join(aqui, "README.md"), encoding="utf-8") as f:
    descripcion = f.read()

# pylint: disable=W0122

metadata = {}
with open("now_lms/version.py", encoding="utf-8") as fp:
    exec(fp.read(), metadata)

setup(
    name="now_lms",
    version=metadata["VERSION"],
    author=metadata["APPAUTHOR"],
    author_email="williamjmorenor@gmail.com",
    description="Simple to {install, use, configure, mantain} learning management system.",
    long_description=descripcion,
    long_description_content_type="text/markdown",
    packages=["now_lms"],
    include_package_data=True,
)
