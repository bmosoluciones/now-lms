def pytest_addoption(parser):
    parser.addoption("--slow", action="store", default="False", help="Run all tests, even those that take the longest.")
