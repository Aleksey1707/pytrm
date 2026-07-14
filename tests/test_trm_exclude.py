import pytest

import pytrm
from tests import contexts
from tests.stubs import DummyTransaction, StubTransactionManager

pytestmark = pytest.mark.asyncio


async def test_exclude_commit(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    with pytest.raises(NeedToCommitException):
        async with transaction_manager.do(context, exclude=(NeedToCommitException,)) as new_context:
            raise NeedToCommitException

    tr = new_context.find(settings.key)
    assert isinstance(tr, DummyTransaction)
    assert tr.is_commited is True
    assert tr.is_rollbacked is False


async def test_exclude_rollback(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    with pytest.raises(ValueError):
        async with transaction_manager.do(context, exclude=(NeedToCommitException,)) as new_context:
            raise ValueError

    tr = new_context.find(settings.key)
    assert isinstance(tr, DummyTransaction)
    assert tr.is_commited is False
    assert tr.is_rollbacked is True


class NeedToCommitException(Exception):
    pass


@pytest.fixture(scope="module")
def transaction_manager(
    settings: pytrm.UniqSettings,
) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = StubTransactionManager.create(settings.id)
    return transaction_manager
