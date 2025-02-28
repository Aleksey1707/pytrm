import dataclasses
import sys
from typing import Callable, Optional

import pytest

import pytrm
from pytrm import bases, exceptions, share
from tests import contexts

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


pytestmark = pytest.mark.asyncio


async def test_transactional(
    service: "StubTransactionalService",
    settings: pytrm.Settings,
    registry: pytrm.Registry,
    context: contexts.Context,
) -> None:
    def func(ctx: contexts.Context) -> None:
        assert ctx is not context

        session = ctx.find(settings.key)
        assert type(session) is DummyTransaction

    await service.process(func, context=context)

    assert context.find(settings.key) is None


async def test_transactional_with_params(
    with_params_service: "StubTransactionalWithParamsService",
    settings: pytrm.Settings,
    registry: pytrm.Registry,
    context: contexts.Context,
) -> None:
    def func(ctx: contexts.Context) -> None:
        assert ctx is not context

        session = ctx.find(settings.key)
        assert type(session) is DummyTransaction

    await with_params_service.process(func, context=context)

    assert context.find(settings.key) is None


# ==============================


@dataclasses.dataclass(frozen=True)
class StubTransactionalService:

    _transaction_manager: pytrm.TransactionManager
    _transaction_manager_settings: Optional[pytrm.Settings]

    @pytrm.transactional
    async def process(self, func: Callable[[contexts.Context], None], *, context: contexts.Context) -> None:
        func(context)


@dataclasses.dataclass(frozen=True)
class StubTransactionalWithParamsService:

    _trm: pytrm.TransactionManager
    _trm_settings: Optional[pytrm.Settings]

    @pytrm.transactional_with("_trm", "_trm_settings")
    async def process(self, func: Callable[[contexts.Context], None], *, context: contexts.Context) -> None:
        func(context)


class DummyNativeTransaction:

    __slosts__ = ()


class DummyTransaction:

    __slots__ = ("_is_active",)

    def __init__(self) -> None:
        self._is_active = False

    def is_active(self) -> bool:
        return self._is_active

    async def begin(self) -> None:
        self._is_active = True

    async def commit(self) -> None:
        self._is_active = False

    async def rollback(self) -> None:
        self._is_active = False

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


@pytest.fixture(scope="module")
def service(
    transaction_manager: pytrm.TransactionManager,
) -> StubTransactionalService:
    return StubTransactionalService(
        _transaction_manager=transaction_manager,
        _transaction_manager_settings=None,
    )


@pytest.fixture(scope="module")
def with_params_service(
    transaction_manager: pytrm.TransactionManager,
) -> StubTransactionalWithParamsService:
    return StubTransactionalWithParamsService(
        _trm=transaction_manager,
        _trm_settings=None,
    )
