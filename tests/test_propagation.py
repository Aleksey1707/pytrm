import pytest

import pytrm
from pytrm import exceptions
from tests import contexts
from tests.stubs import DummyTransaction, StubTransactionManager

pytestmark = pytest.mark.asyncio


async def test_required_creates_transaction_when_absent(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context, propagation=pytrm.Propagation.REQUIRED) as new_context:
        assert isinstance(new_context.find(settings.key), DummyTransaction)


async def test_required_reuses_existing_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    # given: внешний блок уже открыл транзакцию
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)

        # when: вложенный блок с REQUIRED
        async with transaction_manager.do(outer_context, propagation=pytrm.Propagation.REQUIRED) as inner_context:
            inner_transaction = inner_context.find(settings.key)

        # then: та же самая транзакция, вложенный блок её не зафиксировал
        assert inner_transaction is outer_transaction
        assert isinstance(outer_transaction, DummyTransaction)
        assert outer_transaction.is_commited is False


async def test_mandatory_raises_without_transaction(
    context: contexts.Context,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    with pytest.raises(exceptions.PropagationMandatoryTrmException):
        async with transaction_manager.do(context, propagation=pytrm.Propagation.MANDATORY):
            pass


async def test_mandatory_reuses_existing_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)

        async with transaction_manager.do(outer_context, propagation=pytrm.Propagation.MANDATORY) as inner_context:
            assert inner_context.find(settings.key) is outer_transaction


async def test_never_runs_without_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    # given: транзакции в контексте нет
    assert context.find(settings.key) is None

    # when: блок с NEVER
    entered = False
    async with transaction_manager.do(context, propagation=pytrm.Propagation.NEVER) as new_context:
        entered = True

        # then: блок выполняется, транзакция не создаётся
        assert new_context.find(settings.key) is None

    assert entered is True


async def test_never_raises_with_transaction(
    context: contexts.Context,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as outer_context:
        with pytest.raises(exceptions.PropagationNeverTrmException):
            async with transaction_manager.do(outer_context, propagation=pytrm.Propagation.NEVER):
                pass


async def test_not_supported_suspends_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)

        # when: вложенный блок с NOT_SUPPORTED
        async with transaction_manager.do(
            outer_context,
            propagation=pytrm.Propagation.NOT_SUPPORTED,
        ) as inner_context:
            # then: внутри транзакции не видно
            assert inner_context.find(settings.key) is None

        # and: снаружи она осталась и не зафиксирована
        assert outer_context.find(settings.key) is outer_transaction
        assert isinstance(outer_transaction, DummyTransaction)
        assert outer_transaction.is_commited is False


async def test_not_supported_runs_without_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context, propagation=pytrm.Propagation.NOT_SUPPORTED) as new_context:
        assert new_context.find(settings.key) is None


async def test_requires_new_replaces_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)

        # when: вложенный блок с REQUIRES_NEW
        async with transaction_manager.do(outer_context, propagation=pytrm.Propagation.REQUIRES_NEW) as inner_context:
            inner_transaction = inner_context.find(settings.key)

        # then: транзакция другая и уже зафиксирована, внешняя — нет
        assert inner_transaction is not outer_transaction
        assert isinstance(inner_transaction, DummyTransaction)
        assert inner_transaction.is_commited is True
        assert isinstance(outer_transaction, DummyTransaction)
        assert outer_transaction.is_commited is False


async def test_supports_runs_without_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context, propagation=pytrm.Propagation.SUPPORTS) as new_context:
        assert new_context.find(settings.key) is None


async def test_supports_reuses_existing_transaction(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)

        async with transaction_manager.do(outer_context, propagation=pytrm.Propagation.SUPPORTS) as inner_context:
            assert inner_context.find(settings.key) is outer_transaction


async def test_nested_raises_when_not_supported_by_impl(
    context: contexts.Context,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as outer_context:
        with pytest.raises(exceptions.NestedTransactionsNotSupportedTrmException):
            async with transaction_manager.do(outer_context, propagation=pytrm.Propagation.NESTED):
                pass


@pytest.fixture(scope="module")
def transaction_manager(settings: pytrm.UniqSettings) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = StubTransactionManager.create(settings.id)
    return transaction_manager
