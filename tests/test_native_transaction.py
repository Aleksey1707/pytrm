import pytest

import pytrm
from pytrm import exceptions, share
from tests import contexts
from tests.stubs import DummyNativeTransaction, StubTransactionManager

pytestmark = pytest.mark.asyncio


async def test_find_returns_none_when_no_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> None:
    assert pytrm.find_native_transaction(context, settings.id, reg=registry) is None


async def test_find_returns_native_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        native = pytrm.find_native_transaction(new_context, settings.id, reg=registry)

        assert isinstance(native, DummyNativeTransaction)


async def test_find_raises_on_unknown_settings_id(
    context: contexts.Context,
    registry: pytrm.Registry,
) -> None:
    with pytest.raises(exceptions.SettingsNotFoundException):
        pytrm.find_native_transaction(context, "missing", reg=registry)


async def test_find_raises_on_uninitialized_registry(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
) -> None:
    with pytest.raises(exceptions.RegistryIsNotInitializedException):
        pytrm.find_native_transaction(context, settings.id, reg=share.Registry())


async def test_find_raises_on_unknown_value_in_context(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> None:
    spoiled_context = context.set(settings.key, object())

    with pytest.raises(exceptions.UnknownValueInContextException):
        pytrm.find_native_transaction(spoiled_context, settings.id, reg=registry)


async def test_get_returns_native_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        native = pytrm.get_native_transaction(new_context, settings.id, reg=registry)

        assert isinstance(native, DummyNativeTransaction)


async def test_get_raises_when_no_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> None:
    with pytest.raises(exceptions.TransactionNotFoundInContextException):
        pytrm.get_native_transaction(context, settings.id, reg=registry)


@pytest.fixture(scope="module")
def transaction_manager(settings: pytrm.UniqSettings) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = StubTransactionManager.create(settings.id)
    return transaction_manager
