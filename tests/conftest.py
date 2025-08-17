import pytest
from pytest_asyncio import is_async_test

import pytrm
from tests import contexts


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture
def context() -> contexts.Context:
    return contexts.Context.empty()


@pytest.fixture(scope="session")
def settings() -> pytrm.UniqSettings:
    return pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )


@pytest.fixture(scope="session")
def registry(settings: pytrm.UniqSettings) -> pytrm.Registry:
    return pytrm.get_configurated_reg(
        "_transaction_manager",
        "_transaction_manager_settings",
        settings,
    )


@pytest.fixture(scope="session", autouse=True)
def init_default_registry(
    registry: pytrm.Registry,
    settings: pytrm.UniqSettings,
) -> None:
    pytrm.configurate(
        registry.get_trm_attr_name(),
        registry.get_trm_settings_attr_name(),
        settings,
    )
