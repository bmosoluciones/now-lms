"""
Test cases for the coupon system functionality.
"""

from datetime import datetime, timedelta
from unittest import TestCase


class TestCouponSystem(TestCase):
    def setUp(self):
        from now_lms import app, database
        from now_lms.db import Curso, Usuario

        self.app = app
        self.app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "WTF_CSRF_ENABLED": False,
            }
        )

        with self.app.app_context():
            database.create_all()

            # Create test instructor
            self.instructor = Usuario(
                usuario="instructor_test",
                nombre="Test",
                apellido="Instructor",
                correo_electronico="instructor@test.com",
                tipo="instructor",
                activo=True,
                acceso=b"test_password_hash",
            )

            # Create test student
            self.student = Usuario(
                usuario="student_test",
                nombre="Test",
                apellido="Student",
                correo_electronico="student@test.com",
                tipo="user",
                activo=True,
                acceso=b"test_password_hash",
            )

            # Create test paid course
            self.paid_course = Curso(
                nombre="Test Paid Course",
                codigo="TESTPAID",
                descripcion_corta="A test paid course",
                descripcion="A test paid course for coupon testing",
                estado="open",
                publico=True,
                pagado=True,
                precio=100.00,
            )

            # Create test free course
            self.free_course = Curso(
                nombre="Test Free Course",
                codigo="TESTFREE",
                descripcion_corta="A test free course",
                descripcion="A test free course",
                estado="open",
                publico=True,
                pagado=False,
                precio=0.00,
            )

            database.session.add(self.instructor)
            database.session.add(self.student)
            database.session.add(self.paid_course)
            database.session.add(self.free_course)
            database.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        database.session.remove()
        eliminar_base_de_datos_segura()
        database.session.close()
        self.app_context.pop()

    def test_coupon_model_creation(self):
        """Test basic coupon model creation and validation."""
        from now_lms.db import Coupon, database

        with self.app.app_context():
            # Refresh objects to ensure they're bound to current session
            paid_course = database.session.merge(self.paid_course)
            instructor = database.session.merge(self.instructor)

            # Test percentage coupon
            coupon = Coupon(
                course_id=paid_course.codigo,
                code="TEST50",
                discount_type="percentage",
                discount_value=50.0,
                max_uses=10,
                expires_at=datetime.now() + timedelta(days=30),
                created_by=instructor.usuario,
            )

            database.session.add(coupon)
            database.session.commit()

            # Test validation
            is_valid, error = coupon.is_valid()
            self.assertTrue(is_valid)
            self.assertEqual(error, "")

            # Test discount calculation
            discount = coupon.calculate_discount(100.0)
            self.assertEqual(discount, 50.0)

            final_price = coupon.calculate_final_price(100.0)
            self.assertEqual(final_price, 50.0)

    def test_coupon_validation_expired(self):
        """Test coupon validation for expired coupons."""
        from now_lms.db import Coupon, database

        with self.app.app_context():
            # Refresh objects to ensure they're bound to current session
            paid_course = database.session.merge(self.paid_course)
            instructor = database.session.merge(self.instructor)

            # Create expired coupon
            expired_coupon = Coupon(
                course_id=paid_course.codigo,
                code="EXPIRED",
                discount_type="percentage",
                discount_value=25.0,
                expires_at=datetime.now() - timedelta(days=1),
                created_by=instructor.usuario,
            )

            database.session.add(expired_coupon)
            database.session.commit()

            is_valid, error = expired_coupon.is_valid()
            self.assertFalse(is_valid)
            self.assertEqual(error, "Cupón expirado")

    def test_coupon_validation_max_uses(self):
        """Test coupon validation for usage limits."""
        from now_lms.db import Coupon, database

        with self.app.app_context():
            # Refresh objects to ensure they're bound to current session
            paid_course = database.session.merge(self.paid_course)
            instructor = database.session.merge(self.instructor)

            # Create coupon with usage limit
            limited_coupon = Coupon(
                course_id=paid_course.codigo,
                code="LIMITED",
                discount_type="percentage",
                discount_value=25.0,
                max_uses=1,
                current_uses=1,
                created_by=instructor.usuario,
            )

            database.session.add(limited_coupon)
            database.session.commit()

            is_valid, error = limited_coupon.is_valid()
            self.assertFalse(is_valid)
            self.assertEqual(error, "Cupón ha alcanzado el límite de usos")

    def test_fixed_discount_coupon(self):
        """Test fixed amount discount coupon."""
        from now_lms.db import Coupon, database

        with self.app.app_context():
            # Refresh objects to ensure they're bound to current session
            paid_course = database.session.merge(self.paid_course)
            instructor = database.session.merge(self.instructor)

            # Create fixed discount coupon
            fixed_coupon = Coupon(
                course_id=paid_course.codigo,
                code="FIXED20",
                discount_type="fixed",
                discount_value=20.0,
                created_by=instructor.usuario,
            )

            database.session.add(fixed_coupon)
            database.session.commit()

            # Test discount calculation
            discount = fixed_coupon.calculate_discount(100.0)
            self.assertEqual(discount, 20.0)

            final_price = fixed_coupon.calculate_final_price(100.0)
            self.assertEqual(final_price, 80.0)

            # Test discount cannot exceed price
            discount_high = fixed_coupon.calculate_discount(10.0)
            self.assertEqual(discount_high, 10.0)

            final_price_high = fixed_coupon.calculate_final_price(10.0)
            self.assertEqual(final_price_high, 0.0)

    def test_100_percent_discount(self):
        """Test 100% discount coupon results in free enrollment."""
        from now_lms.db import Coupon, database

        with self.app.app_context():
            # Refresh objects to ensure they're bound to current session
            paid_course = database.session.merge(self.paid_course)
            instructor = database.session.merge(self.instructor)

            # Create 100% discount coupon
            free_coupon = Coupon(
                course_id=paid_course.codigo,
                code="FREE100",
                discount_type="percentage",
                discount_value=100.0,
                created_by=instructor.usuario,
            )

            database.session.add(free_coupon)
            database.session.commit()

            final_price = free_coupon.calculate_final_price(100.0)
            self.assertEqual(final_price, 0.0)

    def test_coupon_validation_functions(self):
        """Test the coupon validation helper functions."""
        from now_lms.vistas.courses import _validate_coupon_for_enrollment
        from now_lms.db import Coupon, database

        with self.app.app_context():
            # Refresh objects to ensure they're bound to current session
            paid_course = database.session.merge(self.paid_course)
            instructor = database.session.merge(self.instructor)
            student = database.session.merge(self.student)

            # Create a valid coupon
            valid_coupon = Coupon(
                course_id=paid_course.codigo,
                code="VALID50",
                discount_type="percentage",
                discount_value=50.0,
                created_by=instructor.usuario,
            )

            database.session.add(valid_coupon)
            database.session.commit()

            # Test validation with valid coupon
            coupon, error1, error2 = _validate_coupon_for_enrollment(paid_course.codigo, "VALID50", student)

            self.assertIsNotNone(coupon)
            self.assertIsNone(error1)
            self.assertIsNone(error2)

            # Test with invalid coupon code
            coupon, error1, error2 = _validate_coupon_for_enrollment(paid_course.codigo, "INVALID", student)

            self.assertIsNone(coupon)
            self.assertIsNone(error1)
            self.assertEqual(error2, "Código de cupón inválido")

    def tearDown(self):
        from now_lms.db import database, eliminar_base_de_datos_segura

        with self.app.app_context():
            database.session.remove()
            eliminar_base_de_datos_segura()


if __name__ == "__main__":
    import unittest

    unittest.main()
