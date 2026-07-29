# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Extra comprehensive unit and integration tests for admin profile routes (now_lms/vistas/profiles/admin.py).
"""

import os
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import OperationalError

from now_lms.auth import proteger_passwd
from now_lms.db import (
    database,
    Usuario,
    Curso,
    Pago,
)


@pytest.fixture
def extra_admin_setup(app, db_session):
    """Sets up a complete set of records for extra admin routing tests."""
    admin = Usuario(
        usuario="admin_prof_ex",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_prof_ex@example.com",
        tipo="admin",
        activo=True,
    )
    student_active = Usuario(
        usuario="stud_active_ex",
        acceso=proteger_passwd("pass"),
        nombre="Student Active",
        correo_electronico="stud_active_ex@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    student_inactive = Usuario(
        usuario="stud_inactive_ex",
        acceso=proteger_passwd("pass"),
        nombre="Student Inactive",
        correo_electronico="stud_inactive_ex@example.com",
        tipo="student",
        activo=False,
        correo_electronico_verificado=False,
    )
    db_session.add_all([admin, student_active, student_inactive])
    db_session.commit()

    return {
        "admin": admin,
        "active": student_active,
        "inactive": student_inactive,
    }


def login(client, username):
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": username, "acceso": "pass"})


def test_admin_panel_kpi_and_stats(client, db_session, extra_admin_setup):
    """Test statistics and metrics displayed on the admin panel."""
    login(client, "admin_prof_ex")
    resp = client.get("/admin/panel")
    assert resp.status_code == 200
    assert b"Inactivos" in resp.data or b"inactivos" in resp.data.lower()


def test_user_activation_deactivation_warnings(client, db_session, extra_admin_setup):
    """Test user activation and inactivation with nonexistent users and warning flashes."""
    login(client, "admin_prof_ex")

    # 1. Nonexistent user on activation -> redirects to admin list
    resp = client.post("/admin/users/set_active/NONEXISTENT", follow_redirects=False)
    assert resp.status_code == 302

    # 2. Nonexistent user on inactivation -> redirects to admin list
    resp = client.post("/admin/users/set_inactive/NONEXISTENT", follow_redirects=False)
    assert resp.status_code == 302

    # 3. Activating an already active user -> redirects, no state change
    active_user = extra_admin_setup["active"]
    resp = client.post(f"/admin/users/set_active/{active_user.id}", follow_redirects=False)
    assert resp.status_code == 302
    db_session.refresh(active_user)
    assert active_user.activo is True

    # 4. Inactivating an already inactive user -> redirects, no state change
    inactive_user = extra_admin_setup["inactive"]
    resp = client.post(f"/admin/users/set_inactive/{inactive_user.id}", follow_redirects=False)
    assert resp.status_code == 302
    db_session.refresh(inactive_user)
    assert inactive_user.activo is False


def test_user_email_verification_rejection_errors(client, db_session, extra_admin_setup):
    """Test verification and rejection of unverified users with nonexistent records and demo restrictions."""
    login(client, "admin_prof_ex")

    # 1. Nonexistent user on verification -> redirects, does not fail
    resp = client.post("/admin/users/verify_email/NONEXISTENT", follow_redirects=False)
    assert resp.status_code == 302

    # 2. Nonexistent user on rejection -> redirects, does not fail
    resp = client.post("/admin/users/reject_unverified/NONEXISTENT", follow_redirects=False)
    assert resp.status_code == 302

    # 3. Test verification success
    inactive_user = extra_admin_setup["inactive"]
    resp = client.post(f"/admin/users/verify_email/{inactive_user.id}", follow_redirects=False)
    assert resp.status_code == 302
    db_session.refresh(inactive_user)
    assert inactive_user.correo_electronico_verificado is True
    assert inactive_user.activo is True

    # 4. Test database error on email verification -> rollback
    inactive_user.correo_electronico_verificado = False  # Reset
    db_session.commit()

    with patch("now_lms.vistas.profiles.admin.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        resp = client.post(f"/admin/users/verify_email/{inactive_user.id}", follow_redirects=False)
        assert resp.status_code == 302

    # 5. Test database error on rejection -> rollback
    with patch("now_lms.vistas.profiles.admin.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        resp = client.post(f"/admin/users/reject_unverified/{inactive_user.id}", follow_redirects=False)
        assert resp.status_code == 302


def test_change_user_type_redirects_and_restrictions(client, db_session, extra_admin_setup):
    """Test user type changes with different redirect targets and demo mode restrictions."""
    login(client, "admin_prof_ex")

    # 1. Test success change type with list redirect
    active_user = extra_admin_setup["active"]
    resp = client.post(
        "/admin/user/change_type",
        data={
            "user": active_user.usuario,
            "type": "instructor",
            "redirect_to": "list",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    db_session.refresh(active_user)
    assert active_user.tipo == "instructor"

    # 2. Test success change type with profile redirect
    resp = client.post(
        "/admin/user/change_type",
        data={
            "user": active_user.usuario,
            "type": "student",
            "redirect_to": "profile",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    db_session.refresh(active_user)
    assert active_user.tipo == "student"

    # 3. Test change user type with demo restrictions enabled
    with patch("now_lms.demo_mode.demo_restriction_check", return_value=True):
        # Redirect to profile
        resp = client.post(
            "/admin/user/change_type",
            data={
                "user": active_user.usuario,
                "type": "instructor",
                "redirect_to": "profile",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        # Check that it did not change because of demo restrictions
        db_session.refresh(active_user)
        assert active_user.tipo == "student"


def test_payments_filtering_date_range_value_errors(client, db_session, extra_admin_setup):
    """Test payments route filtering with invalid range strings and value errors."""
    login(client, "admin_prof_ex")

    # Request with invalid end_date format -> triggers ValueError block, redirects/renders
    resp = client.get(
        "/admin/payments",
        query_string={
            "start_date": "2026-01-01",
            "end_date": "invalid-date",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 200


def test_list_inactive_and_unverified_users_rendering(client, db_session, extra_admin_setup):
    """Test inactive and unverified user list views."""
    login(client, "admin_prof_ex")

    resp = client.get("/admin/users/list_inactive")
    assert resp.status_code == 200

    resp = client.get("/admin/users/list_unverified")
    assert resp.status_code == 200


def test_eliminar_usuario_route(client, db_session, extra_admin_setup):
    """Test administrative user deletion."""
    login(client, "admin_prof_ex")
    active_user = extra_admin_setup["active"]

    resp = client.post(
        f"/admin/users/delete/{active_user.id}",
        data={"ruta": "admin_profile.usuarios"},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    deleted_user = db_session.get(Usuario, active_user.id)
    assert deleted_user is None
