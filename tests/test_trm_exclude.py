import sys

import pytest

import pytrm
from pytrm import bases, exceptions, share
from tests import contexts

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


pytestmark = pytest.mark.asyncio


async def test_exclude_commit(
    context: contexts.Context,
    settings: pytrm.Settings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    try:
        async with transaction_manager.do(context, exclude=(NeedToCommitException,)) as new_context:
            raise NeedToCommitException
    except NeedToCommitException:
        tr = new_context.find(settings.key)
        assert isinstance(tr, DummyTransaction)

        assert tr.is_commited is True
        assert tr.is_rollbacked is False


async def test_exclude_rollback(
    context: contexts.Context,
    settings: pytrm.Settings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    try:
        async with transaction_manager.do(context, exclude=(NeedToCommitException,)) as new_context:
            raise ValueError
    except ValueError:
        tr = new_context.find(settings.key)
        assert isinstance(tr, DummyTransaction)

        assert tr.is_commited is False
        assert tr.is_rollbacked is True


# ==============================


class NeedToCommitException(Exception):
    pass


class DummyNativeTransaction:

    __slosts__ = ()


class DummyTransaction:

    def __init__(self) -> None:
        self._is_active = False
        self.is_commited = False
        self.is_rollbacked = False

    def is_active(self) -> bool:
        return self._is_active

    async def begin(self) -> None:
        self._is_active = True

    async def commit(self) -> None:
        self._is_active = False
        self.is_commited = True

    async def rollback(self) -> None:
        self._is_active = False
        self.is_rollbacked = True

    def unwrap(self) -> pytrm.NativeTransaction:
        return DummyNativeTransaction()


class StubTransactionManager(bases.BaseTransactionManager):

    @classmethod
    def create(
        cls,
        settings_id: share.SettingsID,
        *,
        reg: share.Registry = share.DEFAULT_REGISTRY,
    ) -> Self:
        ctx_manager = reg.get_ctx_manager()
        settings = reg.get_settings_by_id(settings_id)

        return cls(
            ctx_manager=ctx_manager,
            settings=settings,
        )

    async def _create_transaction(self) -> share.Transaction:
        return DummyTransaction()

    async def _create_nested_transaction(self) -> share.Transaction:
        raise exceptions.NestedTransactionsNotSupportedTrmException


@pytest.fixture(scope="module")
def transaction_manager(
    settings: pytrm.Settings,
) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = StubTransactionManager.create(settings.id)
    return transaction_manager
