# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios para las funciones auxiliares y decoradores de auth.py.
"""

import pytest
from flask import Flask, session
from flask_login import login_user, logout_user
from now_lms.db import database, Usuario, Configuracion, MailConfig
from now_lms.auth import (
    proteger_passwd,
    validar_acceso,
    usuario_requiere_verificacion_email,
    perfil_requerido,
    email_verificado_requerido,
    proteger_secreto,
    descifrar_secreto,
    generate_confirmation_token,
    validate_confirmation_token,
    send_confirmation_email,
    generate_password_reset_token,
    validate_password_reset_token,
    send_password_reset_email,
)

def _get_or_create_config(db_session):
    """Obtiene la configuración existente o crea una nueva."""
    config = db_session.execute(database.select(Configuracion)).scalar_one_or_none()
    if not config:
        config = Configuracion(
            titulo="Test LMS",
            verify_user_by_email=False,
            r=b"some-random-salt-16bytes-long!"[:16]
        )
        db_session.add(config)
    else:
        config.r = b"some-random-salt-16bytes-long!"[:16]
    db_session.commit()
    return config

def test_proteger_y_descifrar_secreto(app, db_session):
    """Verifica el cifrado y descifrado de secretos."""
    _get_or_create_config(db_session)

    secret = "mi-secreto-super-seguro"
    cifrado = proteger_secreto(secret)
    assert cifrado != secret.encode()

    descifrado = descifrar_secreto(cifrado)
    assert descifrado == secret

def test_descifrar_secreto_sin_config(app, db_session):
    """Debe devolver None si no hay configuración o si falla el descifrado."""
    # Eliminar configuración para forzar row is None
    db_session.execute(database.delete(Configuracion))
    db_session.commit()
    assert descifrar_secreto(b"somebytes") is None

def test_usuario_requiere_verificacion_email_no_autenticado(app, db_session):
    """Debe devolver False si el usuario no está autenticado."""
    with app.test_request_context():
        assert usuario_requiere_verificacion_email() is False

def test_usuario_requiere_verificacion_email_ya_verificado(app, db_session):
    """Debe devolver False si el usuario ya está verificado."""
    user = Usuario(
        usuario="testuser",
        acceso=proteger_passwd("pass"),
        nombre="Test",
        correo_electronico="test@example.com",
        correo_electronico_verificado=True,
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()

    with app.test_request_context():
        login_user(user)
        assert usuario_requiere_verificacion_email() is False
        logout_user()

def test_usuario_requiere_verificacion_email_pendiente(app, db_session):
    """Debe devolver True o False según la configuración de verificación."""
    user = Usuario(
        usuario="testuser",
        acceso=proteger_passwd("pass"),
        nombre="Test",
        correo_electronico="test@example.com",
        correo_electronico_verificado=False,
        tipo="student",
        activo=True,
    )
    db_session.add(user)

    config = _get_or_create_config(db_session)
    config.verify_user_by_email = True
    db_session.commit()

    with app.test_request_context():
        login_user(user)
        # Con verify_user_by_email=True, debe requerir verificación
        assert usuario_requiere_verificacion_email() is True

        # Cambiando la config a False
        config.verify_user_by_email = False
        db_session.commit()
        assert usuario_requiere_verificacion_email() is False
        logout_user()

def test_decoradores_acceso(app, db_session):
    """Prueba el decorador perfil_requerido y email_verificado_requerido."""
    user = Usuario(
        usuario="student_user",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="student@example.com",
        correo_electronico_verificado=False,
        tipo="student",
        activo=True,
    )
    db_session.add(user)

    config = _get_or_create_config(db_session)
    config.verify_user_by_email = True
    db_session.commit()

    @perfil_requerido("admin")
    def vista_admin():
        return "admin_ok"

    @perfil_requerido(("student", "instructor"))
    def vista_multiple():
        return "multiple_ok"

    @email_verificado_requerido
    def vista_verificada():
        return "verificado_ok"

    with app.test_request_context():
        # No autenticado redirige a login
        response = vista_admin()
        assert response.status_code == 302
        assert "login" in response.headers["Location"]

        login_user(user)
        # Autenticado como student, vista_admin debe fallar con 403 (pero perfil_requerido aborta con 403)
        try:
            vista_admin()
            assert False, "Debe abortar con 403"
        except Exception as e:
            # Flask abort lanza una excepción HTTPException o similar
            pass

        # Vista múltiple debe permitir student
        assert vista_multiple() == "multiple_ok"

        # email_verificado_requerido debe redirigir a perfil del usuario si requiere verificación
        response_verificada = vista_verificada()
        assert response_verificada.status_code == 302
        assert "student_user" in response_verificada.headers["Location"]
        logout_user()

def test_tokens_confirmacion_y_correo(app, db_session):
    """Verifica confirmación de email y envío de correo."""
    user = Usuario(
        usuario="unverified",
        acceso=proteger_passwd("pass"),
        nombre="Unverified User",
        correo_electronico="unverified@example.com",
        correo_electronico_verificado=False,
        tipo="student",
        activo=False,
    )
    db_session.add(user)

    mail_conf = MailConfig(
        MAIL_DEFAULT_SENDER="noreply@example.com",
        MAIL_DEFAULT_SENDER_NAME="NOW LMS",
        email_verificado=True
    )
    db_session.add(mail_conf)
    db_session.commit()

    with app.test_request_context():
        # Generar y validar token
        token = generate_confirmation_token(user.correo_electronico)
        assert len(token) > 0

        res_val = validate_confirmation_token(token)
        assert res_val is True

        # Verificar que el usuario se activó y verificó
        db_session.refresh(user)
        assert user.correo_electronico_verificado is True
        assert user.activo is True

        # Validar token inválido o expirado
        assert validate_confirmation_token("token_invalido") is False
        assert validate_confirmation_token("") is False

        # Probar enviar correo de confirmación
        user.correo_electronico_verificado = False
        db_session.commit()
        send_confirmation_email(user)

def test_tokens_password_reset_y_correo(app, db_session):
    """Verifica el flujo de recuperación de contraseña."""
    user = Usuario(
        usuario="resetuser",
        acceso=proteger_passwd("pass"),
        nombre="Reset User",
        correo_electronico="reset@example.com",
        correo_electronico_verificado=True,
        tipo="student",
        activo=True,
    )
    db_session.add(user)

    mail_conf = MailConfig(
        MAIL_DEFAULT_SENDER="noreply@example.com",
        MAIL_DEFAULT_SENDER_NAME="NOW LMS",
        email_verificado=True
    )
    db_session.add(mail_conf)
    db_session.commit()

    with app.test_request_context():
        token = generate_password_reset_token(user.correo_electronico)
        assert len(token) > 0

        email = validate_password_reset_token(token)
        assert email == user.correo_electronico

        assert validate_password_reset_token("invalid-token") is None

        # Enviar correo
        res_mail = send_password_reset_email(user)
        assert res_mail is True
