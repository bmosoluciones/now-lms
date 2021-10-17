import pytest
from now_lms import init_app


@pytest.fixture(scope="package", autouse=True)
def setup_database():
    init_app()
