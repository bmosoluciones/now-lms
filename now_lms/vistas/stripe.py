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

"""Stripe Payments"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, current_app

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import StripeConfig, database

stripe = Blueprint("stripe", __name__, template_folder=DIRECTORIO_PLANTILLAS, url_prefix="stripe_payment")


@cache.cached(timeout=50)
def check_stripe_enabled():
    with current_app.app_context():
        q = database.session.execute(database.select(StripeConfig)).first()
        return q[0].enable


@cache.cached(timeout=50)
def get_stripe_public_key():
    with current_app.app_context():
        q = database.session.execute(database.select(StripeConfig)).first()
        return q[0].stripe_public_key


@cache.cached(timeout=50)
def get_stripe_private_key():
    with current_app.app_context():
        q = database.session.execute(database.select(StripeConfig)).first()
        return q[0].enable
