import pytest


def pytest_addoption(parser):
    parser.addoption("--skip-execs", action="store_true", help="Skip tests that depend on cgf and c2g to run")


def pytest_configure(config):
    config.addinivalue_line("markers", "execs: mark test as requiring cgf and c2g executables to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-execs"):
        skip_execs = pytest.mark.skip(
            reason="skipping because cgf and c2g are required and --skip-execs was passed"
        )
        for item in items:
            if "execs" in item.keywords:
                item.add_marker(skip_execs)
