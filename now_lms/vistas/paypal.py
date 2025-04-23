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

"""Paypal Payments"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
import braintree
from flask import Blueprint, current_app, request
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import PaypalConfig, database

paypal = Blueprint("paypal", __name__, template_folder=DIRECTORIO_PLANTILLAS, url_prefix="/paypal_checkout")

gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Sandbox,
        merchant_id="use_your_merchant_id",
        public_key="use_your_public_key",
        private_key="use_your_private_key",
    )
)


@cache.cached(timeout=50)
def check_paypal_enabled():
    with current_app.app_context():
        try:
            q = database.session.execute(database.select(PaypalConfig)).first()[0]
            enabled = q.enable
            return enabled
        except OperationalError:
            return False


@paypal.route("/token", methods=["GET"])
@login_required  # No anonimus purchases
def token():
    return gateway.client_token.generate(
        {
            "customer_id": current_user.id,
        }
    )


@paypal.route("/", methods=["POST"])
def create_purchase():
    nonce_from_the_client = request.form["payment_method_nonce"]

    result = gateway.transaction.sale(
        {
            "amount": "10.00",
            "payment_method_nonce": nonce_from_the_client,
            "device_data": device_data_from_the_client,
            "options": {"submit_for_settlement": True},
        }
    )
