def pytest_addoption(parser):
    parser.addoption("--slow", action="store", default="False", help="Run all tests, even those that take the longest.")
    parser.addoption("--testpdf", action="store", default="False", help="Check if pdf generation is posible.")
