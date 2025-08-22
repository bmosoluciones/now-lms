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

"""Test Master Class functionality."""

from datetime import datetime, date, time, timedelta

from now_lms.db import MasterClass, MasterClassEnrollment, Usuario, database


def test_master_class_model_exists(session_basic_db_setup):
    """Test that MasterClass model can be imported."""
    assert MasterClass is not None


def test_master_class_enrollment_model_exists(session_basic_db_setup):
    """Test that MasterClassEnrollment model can be imported."""
    assert MasterClassEnrollment is not None


def test_master_class_creation(isolated_db_session):
    """Test creating a master class."""
    from now_lms.auth import proteger_passwd

    # Create instructor user first
    instructor = Usuario(
        usuario="instructor_test",
        acceso=proteger_passwd("test_password"),
        nombre="Juan",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        correo_electronico_verificado=True,
    )
    isolated_db_session.add(instructor)
    isolated_db_session.flush()  # Flush to get the ID

    # Create master class
    future_date = date.today() + timedelta(days=1)
    master_class = MasterClass(
        title="Test Master Class",
        slug="test-master-class",
        description_public="Test description",
        date=future_date,
        start_time=time(10, 0),
        end_time=time(12, 0),
        is_paid=False,
        platform_name="Zoom",
        platform_url="https://zoom.us/j/test",
        instructor_id=instructor.usuario,
    )
    isolated_db_session.add(master_class)
    isolated_db_session.flush()  # Flush to get the ID

    assert master_class.id is not None
    assert master_class.title == "Test Master Class"
    assert master_class.instructor_id == instructor.usuario


def test_master_class_is_upcoming(minimal_db_setup):
    """Test is_upcoming method."""
    # Create instructor user
    instructor = Usuario(
        usuario="instructor_test2",
        acceso=b"test_password",
        nombre="Juan",
        apellido="Instructor",
        correo_electronico="instructor2@test.com",
        tipo="instructor",
        activo=True,
    )
    database.session.add(instructor)
    database.session.commit()

    # Create future master class
    future_date = date.today() + timedelta(days=7)
    master_class = MasterClass(
        title="Future Master Class",
        slug="future-master-class",
        description_public="Future event",
        date=future_date,
        start_time=time(14, 0),
        end_time=time(16, 0),
        is_paid=False,
        platform_name="Zoom",
        platform_url="https://zoom.us/j/test",
        instructor_id=instructor.usuario,
    )
    database.session.add(master_class)
    database.session.commit()

    assert master_class.is_upcoming() is True


def test_master_class_enrollment(minimal_db_setup):
    """Test master class enrollment."""
    # Create instructor user
    instructor = Usuario(
        usuario="instructor_test3",
        acceso=b"test_password",
        nombre="Juan",
        apellido="Instructor",
        correo_electronico="instructor3@test.com",
        tipo="instructor",
        activo=True,
    )
    database.session.add(instructor)
    database.session.commit()

    # Create student user
    student = Usuario(
        usuario="student_test",
        acceso=b"test_password",
        nombre="Ana",
        apellido="Estudiante",
        correo_electronico="student@test.com",
        tipo="user",
        activo=True,
    )
    database.session.add(student)
    database.session.commit()

    # Create master class
    future_date = date.today() + timedelta(days=7)
    master_class = MasterClass(
        title="Test Enrollment",
        slug="test-enrollment",
        description_public="Test enrollment",
        date=future_date,
        start_time=time(14, 0),
        end_time=time(16, 0),
        is_paid=False,
        platform_name="Zoom",
        platform_url="https://zoom.us/j/test",
        instructor_id=instructor.usuario,
    )
    database.session.add(master_class)
    database.session.commit()

    # Create enrollment
    enrollment = MasterClassEnrollment(master_class_id=master_class.id, user_id=student.usuario, is_confirmed=True)
    database.session.add(enrollment)
    database.session.commit()

    assert enrollment.id is not None
    assert enrollment.master_class_id == master_class.id
    assert enrollment.user_id == student.usuario
    assert enrollment.is_access_granted() is True


def test_master_class_always_free(minimal_db_setup):
    """Test that Master Classes are always free (effective price is 0)."""
    # Create instructor
    instructor = Usuario(usuario="instructor", acceso=b"hashed_password", tipo="instructor")
    database.session.add(instructor)
    database.session.commit()

    # Create Master Class with pricing data (should be ignored)
    future_date = (datetime.now() + timedelta(days=1)).date()
    master_class = MasterClass(
        title="Paid Test Master Class",
        slug="paid-test-master-class",
        description_public="This should still be free",
        date=future_date,
        start_time=time(14, 0),
        end_time=time(16, 0),
        is_paid=True,  # This should be ignored
        price=99.99,  # This should be ignored
        platform_name="Zoom",
        platform_url="https://zoom.us/j/test",
        instructor_id=instructor.usuario,
    )
    database.session.add(master_class)
    database.session.commit()

    # Test that effective price is always 0
    assert master_class.get_effective_price() == 0


def test_certificacion_model_supports_master_class(minimal_db_setup):
    """Test that Certificacion model can reference master classes."""
    from now_lms.db import Certificacion, Certificado

    # Create test user
    user = Usuario(
        usuario="test_user",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        correo_electronico="test@test.com",
        tipo="estudiante",
        activo=True,
    )
    database.session.add(user)

    # Create instructor
    instructor = Usuario(
        usuario="instructor",
        acceso=b"test_password",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
    )
    database.session.add(instructor)

    # Create certificate template
    cert_template = Certificado(code="TESTCERT", titulo="Test Certificate", descripcion="Test certificate template")
    database.session.add(cert_template)
    database.session.commit()

    # Create master class
    future_date = date.today() + timedelta(days=1)
    master_class = MasterClass(
        title="Test Master Class",
        slug="test-master-class",
        description_public="Test description",
        date=future_date,
        start_time=time(10, 0),
        end_time=time(12, 0),
        is_paid=False,
        platform_name="Zoom",
        platform_url="https://zoom.us/j/test",
        instructor_id=instructor.usuario,
        is_certificate=True,
        diploma_template_id=cert_template.code,
    )
    database.session.add(master_class)
    database.session.commit()

    # Create certificate for master class
    certificacion = Certificacion(
        usuario=user.usuario,
        curso=None,  # No course
        master_class_id=master_class.id,  # Master class instead
        certificado=cert_template.code,
        nota=95.0,
    )
    database.session.add(certificacion)
    database.session.commit()

    # Test the certificate
    assert certificacion.id is not None
    assert certificacion.master_class_id == master_class.id
    assert certificacion.curso is None
    assert certificacion.get_content_type() == "masterclass"

    # Test get_content_info method
    content = certificacion.get_content_info()
    assert content is not None
    assert content.title == "Test Master Class"


def test_certificacion_model_supports_course(minimal_db_setup):
    """Test that Certificacion model still works with courses."""
    from now_lms.db import Certificacion, Certificado, Curso

    # Create test user
    user = Usuario(
        usuario="test_user",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        correo_electronico="test@test.com",
        tipo="estudiante",
        activo=True,
    )
    database.session.add(user)

    # Create certificate template
    cert_template = Certificado(code="TEST_CERT", titulo="Test Certificate", descripcion="Test certificate template")
    database.session.add(cert_template)
    database.session.commit()

    # Create course
    course = Curso(
        nombre="Test Course",
        codigo="test-course",
        descripcion_corta="Test description",
        descripcion="Test description",
        estado="open",
    )
    database.session.add(course)
    database.session.commit()

    # Create certificate for course
    certificacion = Certificacion(
        usuario=user.usuario,
        curso=course.codigo,  # Course
        master_class_id=None,  # No master class
        certificado=cert_template.code,
        nota=85.0,
    )
    database.session.add(certificacion)
    database.session.commit()

    # Test the certificate
    assert certificacion.id is not None
    assert certificacion.curso == course.codigo
    assert certificacion.master_class_id is None
    assert certificacion.get_content_type() == "course"

    # Test get_content_info method
    content = certificacion.get_content_info()
    assert content is not None
    assert content.nombre == "Test Course"
