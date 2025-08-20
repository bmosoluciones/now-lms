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

"""Modulo para ejecutar NOW LMS."""
# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import init_app
from now_lms.cli import serve
from now_lms.config import DESARROLLO
from now_lms.logs import log

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------


if __name__ == "__main__":
    environ["FLASK_APP"] = "now_lms"
    log.info("Starting NOW Learning Management System.")
    if DESARROLLO:
        log.trace("Running NOW-LMS with development options.")
        init_app(with_examples=True)
    else:
        log.trace("Starting NOW-LMS as importable module.")
        init_app(with_examples=False)
    serve()
