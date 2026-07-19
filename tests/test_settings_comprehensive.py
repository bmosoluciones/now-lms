# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para la administración y configuración del sistema (vistas/settings.py).
"""

import pytest
from flask_login import login_user, logout_user
from now_lms.db import (
    database,
    Usuario,
    Style,
    Configuracion,
    MailConfig,
    AdSense,
    PaypalConfig,
    ExternalApiKey,
)
from now_lms.auth import proteger_passwd
from now_lms.vistas.settings import invalidar_cache

@pytest.fixture
def settings_setup(app, db_session):
    """Configura los registros requeridos para las pruebas de configuración sin duplicados."""
    admin = db_session.execute(database.select(Usuario).filter_by(usuario="admin_s")).scalars().first()
    if not admin:
        admin = Usuario(
            usuario="admin_s",
            acceso=proteger_passwd("pass"),
            nombre="Admin",
            correo_electronico="admin_s@example.com",
            tipo="admin",
            activo=True,
        )
        db_session.add(admin)

    # Style
    style = db_session.execute(database.select(Style)).scalars().first()
    if not style:
        style = Style(theme="now_lms", custom_logo=False, custom_favicon=False)
        db_session.add(style)
    else:
        style.theme = "now_lms"

    # Configuracion
    config = db_session.execute(database.select(Configuracion)).scalars().first()
    if not config:
        config = Configuracion(
            titulo="NOW LMS",
            descripcion="Test LMS",
            moneda="USD",
            lang="es",
            time_zone="America/New_York",
            verify_user_by_email=False,
            allow_unverified_email_login=True,
            r=b"salt_salt_salt_123",
        )
        db_session.add(config)
    else:
        config.titulo = "NOW LMS"
        config.descripcion = "Test LMS"
        config.moneda = "USD"
        config.lang = "es"
        config.time_zone = "America/New_York"
        config.verify_user_by_email = False
        config.allow_unverified_email_login = True

    # MailConfig
    mail_conf = db_session.execute(database.select(MailConfig)).scalars().first()
    if not mail_conf:
        mail_conf = MailConfig(
            MAIL_SERVER="smtp.example.com",
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USE_SSL=False,
            MAIL_DEFAULT_SENDER="noreply@example.com",
            MAIL_DEFAULT_SENDER_NAME="NOW LMS",
            email_verificado=True,
        )
        db_session.add(mail_conf)
    else:
        mail_conf.MAIL_SERVER = "smtp.example.com"
        mail_conf.MAIL_PORT = 587
        mail_conf.MAIL_USE_TLS = True
        mail_conf.MAIL_USE_SSL = False
        mail_conf.MAIL_DEFAULT_SENDER = "noreply@example.com"
        mail_conf.MAIL_DEFAULT_SENDER_NAME = "NOW LMS"
        mail_conf.email_verificado = True

    # AdSense
    adsense = db_session.execute(database.select(AdSense)).scalars().first()
    if not adsense:
        adsense = AdSense(show_ads=False, pub_id="12345")
        db_session.add(adsense)
    else:
        adsense.show_ads = False
        adsense.pub_id = "12345"

    # Paypal
    paypal_c = db_session.execute(database.select(PaypalConfig)).scalars().first()
    if not paypal_c:
        paypal_c = PaypalConfig(enable=False, sandbox=True, paypal_id="client_id", paypal_sandbox="sandbox_id")
        db_session.add(paypal_c)
    else:
        paypal_c.enable = False
        paypal_c.sandbox = True
        paypal_c.paypal_id = "client_id"
        paypal_c.paypal_sandbox = "sandbox_id"

    db_session.commit()

    return {
        "admin": admin,
        "style": style,
        "config": config,
        "mail": mail_conf,
        "adsense": adsense,
        "paypal": paypal_c,
    }

def test_invalidar_cache(app, db_session):
    """Prueba que invalidar_cache se ejecute sin excepciones."""
    res = invalidar_cache()
    assert res is True

def test_routes_theming(client, db_session, settings_setup):
    """Prueba la personalización de tema, logos y favicons."""
    client.post("/user/login", data={"usuario": "admin_s", "acceso": "pass"})

    response_get = client.get("/setting/theming")
    assert response_get.status_code == 200

    response_post = client.post(
        "/setting/theming",
        data={"style": "classic"},
        follow_redirects=True,
    )
    assert response_post.status_code == 200
    db_session.refresh(settings_setup["style"])
    assert settings_setup["style"].theme == "classic"

def test_routes_configuracion_general(client, db_session, settings_setup):
    """Prueba la actualización de la configuración general."""
    client.post("/user/login", data={"usuario": "admin_s", "acceso": "pass"})

    response_get = client.get("/setting/general")
    assert response_get.status_code == 200

    response_post = client.post(
        "/setting/general",
        data={
            "titulo": "LMS MODIFICADO",
            "descripcion": "Descripción nueva",
            "moneda": "EUR",
            "lang": "en",
            "timezone": "Europe/Madrid",
        },
        follow_redirects=True,
    )
    assert response_post.status_code == 200
    db_session.refresh(settings_setup["config"])
    assert settings_setup["config"].titulo == "LMS MODIFICADO"

def test_routes_mail_and_verify(client, db_session, settings_setup):
    """Prueba la configuración y verificación de correo electrónico."""
    client.post("/user/login", data={"usuario": "admin_s", "acceso": "pass"})

    response_get = client.get("/setting/mail")
    assert response_get.status_code == 200

    response_post = client.post(
        "/setting/mail",
        data={
            "MAIL_SERVER": "smtp.mail.com",
            "MAIL_PORT": "465",
            "MAIL_USE_TLS": False,
            "MAIL_USE_SSL": True,
            "MAIL_USERNAME": "test@mail.com",
            "MAIL_PASSWORD": "newpassword",
            "MAIL_DEFAULT_SENDER": "noreply@mail.com",
            "MAIL_DEFAULT_SENDER_NAME": "LMS",
        },
        follow_redirects=True,
    )
    assert response_post.status_code == 200

    # Redirección de prueba de correo
    response_test = client.get("/setting/mail_check", follow_redirects=True)
    assert response_test.status_code == 200

def test_routes_adsense_and_adstxt(client, db_session, settings_setup):
    """Prueba la configuración de Google AdSense y el archivo ads.txt."""
    client.post("/user/login", data={"usuario": "admin_s", "acceso": "pass"})

    response_get = client.get("/setting/adsense")
    assert response_get.status_code == 200

    response_post = client.post(
        "/setting/adsense",
        data={
            "pub_id": "999999",
            "show_ads": True,
        },
        follow_redirects=True,
    )
    assert response_post.status_code == 200
    db_session.refresh(settings_setup["adsense"])
    assert settings_setup["adsense"].pub_id == "999999"

    # Ver /ads.txt
    client.get("/user/logout")
    response_txt = client.get("/ads.txt")
    assert response_txt.status_code == 200
    assert b"pub-999999" in response_txt.data

def test_routes_api_keys(client, db_session, settings_setup):
    """Prueba la creación y revocación de API keys."""
    client.post("/user/login", data={"usuario": "admin_s", "acceso": "pass"})

    # Crear API Key
    response_create = client.post(
        "/setting/api_keys",
        data={
            "name": "Integration Test Key",
            "allowed_origin": "*",
            "notes": "Prueba",
        },
        follow_redirects=True,
    )
    assert response_create.status_code == 200

    # Obtener API Key en DB
    key = db_session.execute(database.select(ExternalApiKey).filter_by(name="Integration Test Key")).scalars().first()
    assert key is not None
    assert key.active is True

    # Revocar API Key
    response_revoke = client.post(f"/setting/api_keys/{key.id}/revoke", follow_redirects=True)
    assert response_revoke.status_code == 200
    db_session.refresh(key)
    assert key.active is False

def test_routes_stripe_and_paypal(client, db_session, settings_setup):
    """Prueba las rutas de pasarelas de pago (PayPal y Stripe)."""
    client.post("/user/login", data={"usuario": "admin_s", "acceso": "pass"})

    response_stripe = client.get("/setting/stripe")
    assert response_stripe.status_code == 200

    response_paypal_get = client.get("/setting/paypal")
    assert response_paypal_get.status_code == 200
