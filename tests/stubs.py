import sys

import pytrm
from pytrm import bases, exceptions, share

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


class DummyNativeTransaction:
    __slots__ = ()


class DummyTransaction:
    __slots__ = ("_is_active", "is_commited", "is_rollbacked")

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
