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

import pytest

from datetime import date, time

from now_lms.auth import proteger_passwd
from now_lms.db import MasterClass, MasterClassEnrollment, Usuario, database, select


REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_usuario(db_session, usuario: str, tipo: str) -> Usuario:
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd(usuario),
        nombre=f"{tipo.title()} {usuario}",
        correo_electronico=f"{usuario}@example.com",
        tipo=tipo,
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login(app, usuario: str, acceso: str, client=None):
    client = client or app.test_client()
    resp = client.post("/user/login", data={"usuario": usuario, "acceso": acceso}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    location = resp.headers.get("Location", "")
    if location:
        assert "/user/login" not in location, f"Login failed for {usuario}, redirected to {location}"
    return client


@pytest.mark.usefixtures("app", "db_session")
def test_end_to_end_masterclass_flow(app, db_session):
    instructor = _crear_usuario(db_session, "instr_mc", "instructor")
    student = _crear_usuario(db_session, "student_mc", "user")
    admin = _crear_usuario(db_session, "admin_mc", "admin")

    client = _login(app, instructor.usuario, "instr_mc")

    create_payload = {
        "title": "Masterclass de Prueba",
        "description_public": "Descripcion publica extendida para masterclass de prueba.",
        "description_private": "Contenido privado para inscritos.",
        "date": date.today().strftime("%Y-%m-%d"),
        "start_time": time(9, 0).strftime("%H:%M"),
        "end_time": time(10, 0).strftime("%H:%M"),
        "platform_name": "Zoom",
        "platform_url": "https://zoom.us/j/123456789",
        "is_certificate": "",
        "diploma_template_id": "",
        "video_recording_url": "",
    }

    resp_create = client.post("/masterclass/instructor/create", data=create_payload, follow_redirects=False)
    assert resp_create.status_code in REDIRECT_STATUS_CODES | {200}

    master_class = db_session.execute(select(MasterClass).filter_by(title="Masterclass de Prueba")).scalars().first()
    assert master_class is not None
    slug_original = master_class.slug

    resp_public_list = app.test_client().get("/masterclass/")
    assert resp_public_list.status_code == 200
    assert master_class.title.encode() in resp_public_list.data

    resp_public_detail = app.test_client().get(f"/masterclass/{slug_original}")
    assert resp_public_detail.status_code == 200

    # Close instructor session before switching to student
    client.get("/user/logout")

    client = _login(app, student.usuario, "student_mc", client=client)
    # Ensure student session is not elevated to instructor/admin
    resp_student_instructor_page = client.get("/masterclass/instructor")
    assert resp_student_instructor_page.status_code == 403
    resp_enroll_get = client.get(f"/masterclass/{slug_original}/enroll")
    assert resp_enroll_get.status_code == 200

    resp_enroll_post = client.post(f"/masterclass/{slug_original}/enroll", follow_redirects=False)
    assert resp_enroll_post.status_code in REDIRECT_STATUS_CODES | {200}

    database.session.expire_all()
    all_enrollments = database.session.execute(select(MasterClassEnrollment)).scalars().all()
    enrollment_pairs = [(en.master_class_id, en.user_id) for en in all_enrollments]
    enrollment = (
        database.session.execute(
            select(MasterClassEnrollment).filter_by(master_class_id=master_class.id, user_id=student.usuario)
        )
        .scalars()
        .first()
    )
    assert enrollment is not None, (
        f"Enrollment missing; status={resp_enroll_post.status_code}, "
        f"location={resp_enroll_post.headers.get('Location')}, "
        f"total={len(all_enrollments)}, pairs={enrollment_pairs}"
    )
    assert enrollment.is_confirmed is True

    resp_my_enrollments = client.get("/masterclass/my-enrollments")
    assert resp_my_enrollments.status_code == 200
    assert master_class.title.encode() in resp_my_enrollments.data

    resp_enroll_again = client.post(f"/masterclass/{slug_original}/enroll", follow_redirects=False)
    assert resp_enroll_again.status_code in REDIRECT_STATUS_CODES | {200}
    enrollments = (
        database.session.execute(
            select(MasterClassEnrollment).filter_by(master_class_id=master_class.id, user_id=student.usuario)
        )
        .scalars()
        .all()
    )
    assert len(enrollments) == 1

    # Switch back to instructor session to validate instructor-only views
    client.get("/user/logout")
    client = _login(app, instructor.usuario, "instr_mc", client=client)
    resp_instructor_list = client.get("/masterclass/instructor")
    assert resp_instructor_list.status_code == 200
    assert master_class.title.encode() in resp_instructor_list.data

    edit_payload = {
        "title": "Masterclass Editada",
        "description_public": "Descripcion publica editada para masterclass de prueba.",
        "description_private": "Contenido privado actualizado.",
        "date": date.today().strftime("%Y-%m-%d"),
        "start_time": time(11, 0).strftime("%H:%M"),
        "end_time": time(12, 0).strftime("%H:%M"),
        "platform_name": "Zoom",
        "platform_url": "https://zoom.us/j/123456789",
        "is_certificate": "",
        "diploma_template_id": "",
        "video_recording_url": "https://example.com/recording",
    }

    resp_edit = client.post(f"/masterclass/instructor/{master_class.id}/edit", data=edit_payload, follow_redirects=False)
    assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}

    db_session.expire_all()
    master_class_edit = db_session.get(MasterClass, master_class.id)
    assert master_class_edit is not None
    assert master_class_edit.title == "Masterclass Editada"
    assert master_class_edit.slug != slug_original

    resp_public_detail_updated = app.test_client().get(f"/masterclass/{master_class_edit.slug}")
    assert resp_public_detail_updated.status_code == 200

    client.get("/user/logout")
    client = _login(app, admin.usuario, "admin_mc", client=client)
    resp_admin_list = client.get("/masterclass/admin")
    assert resp_admin_list.status_code == 200
    assert master_class_edit.title.encode() in resp_admin_list.data
