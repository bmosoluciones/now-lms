def pytest_addoption(parser):
    parser.addoption("--slow", action="store", default="False", help="Run all tests, even those that take the longest.")
    parser.addoption("--use-cases", action="store", default="False", help="Test common use cases.")
