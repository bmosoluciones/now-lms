"""Test the new_question route fix."""

import pytest
from flask import url_for


def test_new_question_route_exists(client, full_db_setup):
    """Test that the new_question route exists and can generate URLs."""

    # Login as admin to access instructor routes
    client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})

    # Test that we can generate the URL
    with client.application.app_context():
        try:
            test_evaluation_id = "01HNZXJRD65A55BJACFEFNZ88D"
            url = url_for("instructor_profile.new_question", evaluation_id=test_evaluation_id)
            assert url is not None
            assert "questions/new" in url
            print(f"✓ Successfully generated URL: {url}")
        except Exception as e:
            pytest.fail(f"Failed to generate URL for new_question route: {e}")


def test_new_question_route_in_url_map(client):
    """Test that the new_question route is registered in the URL map."""

    with client.application.app_context():
        found_route = False
        for rule in client.application.url_map.iter_rules():
            if "new_question" in rule.endpoint:
                found_route = True
                print(f"✓ Found route: {rule.endpoint} -> {rule.rule}")
                break

        assert found_route, "new_question route not found in URL map"


def test_new_question_route_access_with_evaluation(client, full_db_setup):
    """Test that the new_question route can be accessed with a valid evaluation."""

    # Login as admin
    client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})

    # Create a course and section first
    course_data = {
        "codigo": "test_course",
        "nombre": "Test Course",
        "descripcion": "Test course for new question route",
        "descripcion_corta": "Test course description",
        "nivel": 0,
        "publico": True,
        "modalidad": "self_paced",
        "pagado": False,
        "auditable": False,
        "certificado": False,
        "precio": 0,
    }

    client.post("/course/new_curse", data=course_data)

    # Create a section
    section_data = {
        "nombre": "Test Section",
        "descripcion": "Test section",
    }

    client.post("/course/test_course/new_seccion", data=section_data)

    # Try to access the new question form - should get a response (not necessarily 200, could be redirect)
    with client.application.app_context():
        test_evaluation_id = "01HNZXJRD65A55BJACFEFNZ88D"
        url = url_for("instructor_profile.new_question", evaluation_id=test_evaluation_id)

    response = client.get(url)
    # Even if evaluation doesn't exist, we should get a redirect or error page, not a 404
    assert response.status_code != 404, f"Route not found: {url}"
