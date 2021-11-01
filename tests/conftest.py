import pytest
from now_lms import init_app, lms_app


lms_app.app_context().push()

@pytest.fixture(scope="package", autouse=True)
def setup_database():
    init_app()
