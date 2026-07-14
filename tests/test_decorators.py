import dataclasses
from typing import Callable, Optional

import pytest

import pytrm
from tests import contexts
from tests.stubs import DummyTransaction, StubTransactionManager

pytestmark = pytest.mark.asyncio


async def test_transactional(
    service: "StubTransactionalService",
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
    context: contexts.Context,
) -> None:
    # given: callback с проверками, которые должны сработать внутри транзакции
    def func(ctx: contexts.Context) -> None:
        assert ctx is not context
        session = ctx.find(settings.key)
        assert type(session) is DummyTransaction

    # when: декоратор оборачивает вызов в транзакцию
    await service.process(func, context=context)

    # then: исходный контекст не содержит транзакцию
    assert context.find(settings.key) is None


async def test_transactional_with_params(
    with_params_service: "StubTransactionalWithParamsService",
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
    context: contexts.Context,
) -> None:
    # given: callback с проверками, которые должны сработать внутри транзакции
    def func(ctx: contexts.Context) -> None:
        assert ctx is not context
        session = ctx.find(settings.key)
        assert type(session) is DummyTransaction

    # when: transactional_with оборачивает вызов в транзакцию
    await with_params_service.process(func, context=context)

    # then: исходный контекст не содержит транзакцию
    assert context.find(settings.key) is None


@dataclasses.dataclass(frozen=True)
class StubTransactionalService:
    _transaction_manager: pytrm.TransactionManager
    _transaction_manager_settings: Optional[pytrm.UniqSettings]

    @pytrm.transactional
    async def process(self, func: Callable[[contexts.Context], None], *, context: contexts.Context) -> None:
        func(context)


@dataclasses.dataclass(frozen=True)
class StubTransactionalWithParamsService:
    _trm: pytrm.TransactionManager
    _trm_settings: Optional[pytrm.UniqSettings]

    @pytrm.transactional_with("_trm", "_trm_settings")
    async def process(self, func: Callable[[contexts.Context], None], *, context: contexts.Context) -> None:
        func(context)


@pytest.fixture(scope="module")
def transaction_manager(
    settings: pytrm.UniqSettings,
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
