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


async def test_transactional_with_propagation_override_explicit_settings(
    transaction_manager: pytrm.TransactionManager,
    settings: pytrm.UniqSettings,
    context: contexts.Context,
) -> None:
    # given: настройки компонента с REQUIRED, декоратор переопределяет на REQUIRES_NEW
    required_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.REQUIRED)
    service = StubTransactionalWithPropagationService(
        _trm=transaction_manager,
        _trm_settings=required_settings,
    )

    # when: вызов внутри уже открытой транзакции
    outer_transaction = None
    inner_transaction = None
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)
        inner_context = await service.process_isolated(context=outer_context)
        inner_transaction = inner_context.find(settings.key)

    # then: внутренняя транзакция отделена от внешней
    assert inner_transaction is not outer_transaction


async def test_transactional_with_propagation_override_when_settings_none(
    transaction_manager: pytrm.TransactionManager,
    settings: pytrm.UniqSettings,
    context: contexts.Context,
) -> None:
    # given: настройки компонента отсутствуют, override применяется к дефолту менеджера
    service = StubTransactionalWithPropagationService(
        _trm=transaction_manager,
        _trm_settings=None,
    )

    # when: вызов внутри уже открытой транзакции
    outer_transaction = None
    inner_transaction = None
    async with transaction_manager.do(context) as outer_context:
        outer_transaction = outer_context.find(settings.key)
        inner_context = await service.process_isolated(context=outer_context)
        inner_transaction = inner_context.find(settings.key)

    # then: внутренняя транзакция отделена от внешней
    assert inner_transaction is not outer_transaction


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


@dataclasses.dataclass(frozen=True)
class StubTransactionalWithPropagationService:
    _trm: pytrm.TransactionManager
    _trm_settings: Optional[pytrm.UniqSettings]

    @pytrm.transactional_with("_trm", "_trm_settings", propagation=pytrm.Propagation.REQUIRES_NEW)
    async def process_isolated(self, *, context: contexts.Context) -> contexts.Context:
        return context


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
