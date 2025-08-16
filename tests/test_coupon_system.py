"""
Test cases for the coupon system functionality.
"""

from datetime import datetime, timedelta

from now_lms.db import database, Curso, Usuario


def test_coupon_model_creation(minimal_db_setup):
    """Test basic coupon model creation and validation."""
    from now_lms.db import Coupon

    # Create test instructor
    instructor = Usuario(
        usuario="instructor_test",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test paid course
    paid_course = Curso(
        nombre="Test Paid Course",
        codigo="TESTPAID",
        descripcion_corta="A test paid course",
        descripcion="A test paid course for coupon testing",
        estado="open",
        publico=True,
        pagado=True,
        precio=100.00,
    )

    database.session.add(instructor)
    database.session.add(paid_course)
    database.session.commit()

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
    assert is_valid
    assert error == ""

    # Test discount calculation
    discount = coupon.calculate_discount(100.0)
    assert discount == 50.0

    final_price = coupon.calculate_final_price(100.0)
    assert final_price == 50.0


def test_coupon_validation_expired(minimal_db_setup):
    """Test coupon validation for expired coupons."""
    from now_lms.db import Coupon

    # Create test instructor
    instructor = Usuario(
        usuario="instructor_test",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test paid course
    paid_course = Curso(
        nombre="Test Paid Course",
        codigo="TESTPAID",
        descripcion_corta="A test paid course",
        descripcion="A test paid course for coupon testing",
        estado="open",
        publico=True,
        pagado=True,
        precio=100.00,
    )

    database.session.add(instructor)
    database.session.add(paid_course)
    database.session.commit()

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
    assert not is_valid
    assert error == "Cupón expirado"


def test_coupon_validation_max_uses(minimal_db_setup):
    """Test coupon validation for usage limits."""
    from now_lms.db import Coupon

    # Create test instructor
    instructor = Usuario(
        usuario="instructor_test",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test paid course
    paid_course = Curso(
        nombre="Test Paid Course",
        codigo="TESTPAID",
        descripcion_corta="A test paid course",
        descripcion="A test paid course for coupon testing",
        estado="open",
        publico=True,
        pagado=True,
        precio=100.00,
    )

    database.session.add(instructor)
    database.session.add(paid_course)
    database.session.commit()

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
    assert not is_valid
    assert error == "Cupón ha alcanzado el límite de usos"


def test_fixed_discount_coupon(minimal_db_setup):
    """Test fixed amount discount coupon."""
    from now_lms.db import Coupon

    # Create test instructor
    instructor = Usuario(
        usuario="instructor_test",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test paid course
    paid_course = Curso(
        nombre="Test Paid Course",
        codigo="TESTPAID",
        descripcion_corta="A test paid course",
        descripcion="A test paid course for coupon testing",
        estado="open",
        publico=True,
        pagado=True,
        precio=100.00,
    )

    database.session.add(instructor)
    database.session.add(paid_course)
    database.session.commit()

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
    assert discount == 20.0

    final_price = fixed_coupon.calculate_final_price(100.0)
    assert final_price == 80.0

    # Test discount cannot exceed price
    discount_high = fixed_coupon.calculate_discount(10.0)
    assert discount_high == 10.0

    final_price_high = fixed_coupon.calculate_final_price(10.0)
    assert final_price_high == 0.0


def test_100_percent_discount(minimal_db_setup):
    """Test 100% discount coupon results in free enrollment."""
    from now_lms.db import Coupon

    # Create test instructor
    instructor = Usuario(
        usuario="instructor_test",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test paid course
    paid_course = Curso(
        nombre="Test Paid Course",
        codigo="TESTPAID",
        descripcion_corta="A test paid course",
        descripcion="A test paid course for coupon testing",
        estado="open",
        publico=True,
        pagado=True,
        precio=100.00,
    )

    database.session.add(instructor)
    database.session.add(paid_course)
    database.session.commit()

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
    assert final_price == 0.0


def test_coupon_validation_functions(minimal_db_setup):
    """Test the coupon validation helper functions."""
    from now_lms.vistas.courses import _validate_coupon_for_enrollment
    from now_lms.db import Coupon

    # Create test instructor
    instructor = Usuario(
        usuario="instructor_test",
        nombre="Test",
        apellido="Instructor",
        correo_electronico="instructor@test.com",
        tipo="instructor",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test student
    student = Usuario(
        usuario="student_test",
        nombre="Test",
        apellido="Student",
        correo_electronico="student@test.com",
        tipo="user",
        activo=True,
        acceso=b"test_password_hash",
    )

    # Create test paid course
    paid_course = Curso(
        nombre="Test Paid Course",
        codigo="TESTPAID",
        descripcion_corta="A test paid course",
        descripcion="A test paid course for coupon testing",
        estado="open",
        publico=True,
        pagado=True,
        precio=100.00,
    )

    database.session.add(instructor)
    database.session.add(student)
    database.session.add(paid_course)
    database.session.commit()

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

    assert coupon is not None
    assert error1 is None
    assert error2 is None

    # Test with invalid coupon code
    coupon, error1, error2 = _validate_coupon_for_enrollment(paid_course.codigo, "INVALID", student)

    assert coupon is None
    assert error1 is None
    assert error2 == "Código de cupón inválido"
