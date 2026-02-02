# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios para autenticación.

Cada test es independiente, crea sus datos, los valida y los destruye.
Sin código mágico - todo es explícito y fácil de leer.
"""


def test_proteger_passwd_crea_hash():
    """proteger_passwd debe crear un hash diferente a la contraseña original."""
    from now_lms.auth import proteger_passwd

    password = "mi_contraseña"
    hashed = proteger_passwd(password)

    assert hashed != password.encode()
    assert len(hashed) > 0


def test_validar_acceso_con_usuario_valido(app, db_session):
    """validar_acceso debe aceptar credenciales correctas."""
    from now_lms.auth import proteger_passwd, validar_acceso
    from now_lms.db import Usuario

    # Crear usuario con campos mínimos requeridos
    password = "test123"
    user = Usuario(
        usuario="testuser",
        acceso=proteger_passwd(password),
        nombre="Test",
        correo_electronico="test@example.com",
        tipo="student",
        activo=True,
    )

    db_session.add(user)
    db_session.commit()

    # Validar acceso
    result = validar_acceso("testuser", password)
    assert result is True


def test_validar_acceso_con_contraseña_incorrecta(app, db_session):
    """validar_acceso debe rechazar contraseña incorrecta."""
    from now_lms.auth import proteger_passwd, validar_acceso
    from now_lms.db import Usuario

    # Crear usuario
    user = Usuario(
        usuario="testuser2",
        acceso=proteger_passwd("correcta"),
        nombre="Test",
        correo_electronico="test2@example.com",
        tipo="student",
        activo=True,
    )

    db_session.add(user)
    db_session.commit()

    # Validar con contraseña incorrecta
    result = validar_acceso("testuser2", "incorrecta")
    assert result is False
