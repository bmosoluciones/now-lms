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

"""Comprehensive tests for MasterClass functionality - Basic version."""

from datetime import date, time
from decimal import Decimal

from now_lms.db import (
    MasterClass,
    MasterClassEnrollment,
    Certificado,
    Usuario,
    database,
)


class TestMasterClassBasicFunctionality:
    """Test basic MasterClass model and creation."""

    def test_masterclass_model_exists(self, minimal_db_setup):
        """Test that MasterClass model can be imported and instantiated."""
        masterclass = MasterClass(
            title="Test MasterClass",
            slug="test-masterclass",
            description_public="A test masterclass",
            date=date(2025, 12, 31),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/test",
            is_paid=False,
            is_certificate=False,
        )
        assert masterclass is not None
        assert masterclass.title == "Test MasterClass"
        assert masterclass.slug == "test-masterclass"

    def test_masterclass_creation_with_database(self, minimal_db_setup):
        """Test MasterClass creation and persistence in database."""
        # Create instructor
        instructor = Usuario(
            usuario="instructor_user",
            acceso=b"password123",
            nombre="Test",
            apellido="Instructor",
            correo_electronico="instructor@test.com",
            tipo="teacher",
        )
        database.session.add(instructor)
        database.session.commit()

        masterclass = MasterClass(
            title="Database Test MasterClass",
            slug="database-test-masterclass",
            description_public="Testing database persistence",
            date=date(2026, 1, 15),
            start_time=time(14, 0),
            end_time=time(16, 0),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/test",
            is_paid=True,
            price=Decimal("99.99"),
            is_certificate=True,
            instructor_id=instructor.usuario,
        )

        database.session.add(masterclass)
        database.session.commit()

        # Retrieve and verify
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="database-test-masterclass")
        ).scalar_one()

        assert retrieved.title == "Database Test MasterClass"
        assert retrieved.price == Decimal("99.99")
        assert retrieved.is_paid is True
        assert retrieved.is_certificate is True

    def test_masterclass_enrollment(self, minimal_db_setup):
        """Test user enrollment in MasterClass."""
        # Create instructor
        instructor = Usuario(
            usuario="mc_instructor",
            acceso=b"password123",
            nombre="MasterClass",
            apellido="Instructor",
            correo_electronico="mcteacher@test.com",
            tipo="teacher",
        )
        database.session.add(instructor)

        # Create user
        user = Usuario(
            usuario="mc_student",
            acceso=b"password123",
            nombre="MasterClass",
            apellido="Student",
            correo_electronico="mcstudent@test.com",
            tipo="student",
        )
        database.session.add(user)

        # Create MasterClass
        masterclass = MasterClass(
            title="Enrollment Test MasterClass",
            slug="enrollment-test-mc",
            description_public="Testing enrollment",
            date=date(2026, 2, 20),
            start_time=time(9, 0),
            end_time=time(11, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/enrollment-test",
            is_paid=False,
            instructor_id=instructor.usuario,
        )
        database.session.add(masterclass)
        database.session.commit()

        # Enroll user
        enrollment = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id=user.usuario,
            is_confirmed=True,
        )
        database.session.add(enrollment)
        database.session.commit()

        # Verify enrollment
        retrieved = database.session.execute(
            database.select(MasterClassEnrollment).filter_by(master_class_id=masterclass.id, user_id=user.usuario)
        ).scalar_one()

        assert retrieved.is_confirmed is True

    def test_masterclass_with_certification(self, minimal_db_setup):
        """Test MasterClass with certification configuration."""
        # Create instructor
        instructor = Usuario(
            usuario="cert_instructor",
            acceso=b"password123",
            nombre="Cert",
            apellido="Instructor",
            correo_electronico="certteacher@test.com",
            tipo="teacher",
        )
        database.session.add(instructor)

        # Create certificate template
        template = Certificado(
            code="MC_CERT",
            titulo="MasterClass Certificate",
            habilitado=True,
        )
        database.session.add(template)

        # Create MasterClass with certification
        masterclass = MasterClass(
            title="Certification MasterClass",
            slug="cert-masterclass",
            description_public="MasterClass with certificate",
            date=date(2026, 3, 10),
            start_time=time(13, 0),
            end_time=time(15, 0),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/cert-mc",
            is_certificate=True,
            diploma_template_id="MC_CERT",
            instructor_id=instructor.usuario,
        )
        database.session.add(masterclass)
        database.session.commit()

        # Verify certification configuration
        retrieved = database.session.execute(database.select(MasterClass).filter_by(slug="cert-masterclass")).scalar_one()

        assert retrieved.is_certificate is True
        assert retrieved.diploma_template_id == "MC_CERT"
