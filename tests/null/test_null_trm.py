import pytest

import pytrm
from tests import contexts

pytestmark = pytest.mark.asyncio


async def test_null_trm(
    context: contexts.Context,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        assert new_context is not context


async def test_null_trm_does_not_put_transaction_in_context(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        assert new_context.find(settings.key) is None


async def test_null_trm_ignores_settings_and_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    # given: MANDATORY у настоящей реализации потребовал бы существующей транзакции
    mandatory_settings = settings.with_propagation(pytrm.Propagation.MANDATORY)

    # when: null-реализация получает те же настройки
    async with transaction_manager.do(
        context,
        settings=mandatory_settings,
        propagation=pytrm.Propagation.NEVER,
    ) as new_context:
        # then: блок просто выполняется
        assert new_context.find(settings.key) is None


async def test_null_trm_propagates_exception(
    context: contexts.Context,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    with pytest.raises(ValueError):
        async with transaction_manager.do(context, exclude=(ValueError,)):
            raise ValueError
