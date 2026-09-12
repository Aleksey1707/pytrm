import asyncio
from typing import List

import pytest

import pytrm
from tests import contexts
from tests.stubs import DummyTransaction, StubTransactionManager

pytestmark = pytest.mark.asyncio


async def test_cancellation_rolls_back(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    # given: блок, который висит внутри транзакции
    opened: List[DummyTransaction] = []

    async def run() -> None:
        async with transaction_manager.do(context) as new_context:
            transaction = new_context.find(settings.key)
            assert isinstance(transaction, DummyTransaction)
            opened.append(transaction)
            await asyncio.sleep(3600)

    task = asyncio.create_task(run())
    while not opened:
        await asyncio.sleep(0)

    # when: задачу отменяют
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # then: транзакция откачена, а не оставлена открытой
    transaction = opened[0]
    assert transaction.is_rollbacked is True
    assert transaction.is_commited is False
    assert transaction.is_active() is False


async def test_base_exception_rolls_back(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    with pytest.raises(NeedToRollbackBaseException):
        async with transaction_manager.do(context) as new_context:
            raise NeedToRollbackBaseException

    transaction = new_context.find(settings.key)
    assert isinstance(transaction, DummyTransaction)
    assert transaction.is_rollbacked is True
    assert transaction.is_commited is False


async def test_base_exception_in_exclude_commits(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    with pytest.raises(NeedToCommitBaseException):
        async with transaction_manager.do(context, exclude=(NeedToCommitBaseException,)) as new_context:
            raise NeedToCommitBaseException

    transaction = new_context.find(settings.key)
    assert isinstance(transaction, DummyTransaction)
    assert transaction.is_commited is True
    assert transaction.is_rollbacked is False


class NeedToRollbackBaseException(BaseException):
    pass


class NeedToCommitBaseException(BaseException):
    pass


@pytest.fixture(scope="module")
def transaction_manager(settings: pytrm.UniqSettings) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = StubTransactionManager.create(settings.id)
    return transaction_manager
