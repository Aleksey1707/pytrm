import dataclasses
from typing import Any, Final

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import pytrm
from pytrm import exceptions
from tests import contexts
from tests.sqlalchemy.conftest import test_table

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


async def test_required_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    registry: pytrm.Registry,
    sessionmaker_: sessionmaker,
) -> None:
    # given: запись для вставки, транзакции ещё нет
    ID: Final = 1
    stmt: Any
    required_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.REQUIRED)
    assert context.find(required_settings.key) is None

    # when: вставляем запись в транзакции
    async with transaction_manager.do(context) as new_context:
        assert new_context.find(required_settings.key) is not None
        stmt = test_table.insert().values(id=ID, value=0)
        session = _get_session(new_context, required_settings, registry)
        await session.execute(stmt)

    assert context.find(required_settings.key) is None

    # then: запись зафиксирована и видна вне транзакции
    async with sessionmaker_() as session:
        stmt = test_table.select().where(test_table.c.id == ID)
        result = await session.execute(stmt)
        record = result.one()

    assert record.id == ID
    assert record.value == 0


async def test_nested_propagation_rollback(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    registry: pytrm.Registry,
    sessionmaker_: sessionmaker,
) -> None:
    # given: незакоммиченная запись в родительской транзакции
    ID: Final = 2
    stmt: Any

    async with transaction_manager.do(context) as new_context:
        stmt = test_table.insert().values(id=ID, value=0)
        session = _get_session(new_context, settings, registry)
        await session.execute(stmt)

        nested_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.NESTED)

        # when: вложенная транзакция видит изменения родителя, обновляет запись и откатывается
        with pytest.raises(RuntimeError, match="Need rollback nested transaction"):
            async with transaction_manager.do(new_context, settings=nested_settings) as nested_context:
                parent_session = _get_session(new_context, settings, registry)
                nested_session = _get_session(nested_context, settings, registry)
                assert parent_session is nested_session

                stmt = test_table.select().where(test_table.c.id == ID)
                result = await nested_session.execute(stmt)
                record = result.one()
                assert record.value == 0

                stmt = test_table.update().where(test_table.c.id == ID).values(value=9)
                await nested_session.execute(stmt)
                raise RuntimeError("Need rollback nested transaction")

        # and: родительская транзакция остаётся активной и может продолжить работу
        session = _get_session(new_context, settings, registry)
        stmt = test_table.select().where(test_table.c.id == ID)
        result = await session.execute(stmt)
        record = result.one()
        assert record.value == 0

        stmt = test_table.update().where(test_table.c.id == ID).values(value=5)
        await session.execute(stmt)

    # then: изменения из вложенной транзакции не сохранились, родительская транзакция зафиксирована
    async with sessionmaker_() as session:
        stmt = test_table.select().where(test_table.c.id == ID)
        result = await session.execute(stmt)
        record = result.one()

    assert record.id == ID
    assert record.value == 5


async def test_nested_propagation_commit(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    registry: pytrm.Registry,
    sessionmaker_: sessionmaker,
) -> None:
    # given: запись в родительской транзакции
    ID: Final = 3
    stmt: Any

    async with transaction_manager.do(context) as new_context:
        stmt = test_table.insert().values(id=ID, value=0)
        session = _get_session(new_context, settings, registry)
        await session.execute(stmt)

        # when: вложенная транзакция обновляет запись без исключения
        nested_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.NESTED)
        async with transaction_manager.do(new_context, settings=nested_settings) as nested_context:
            session = _get_session(nested_context, settings, registry)
            stmt = test_table.update().where(test_table.c.id == ID).values(value=7)
            await session.execute(stmt)

    # then: изменения из savepoint зафиксированы вместе с родительской транзакцией
    async with sessionmaker_() as session:
        stmt = test_table.select().where(test_table.c.id == ID)
        result = await session.execute(stmt)
        record = result.one()

    assert record.id == ID
    assert record.value == 7


async def test_mandatory_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    mandatory_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.MANDATORY)

    with pytest.raises(exceptions.PropagationMandatoryTrmException):
        async with transaction_manager.do(context, settings=mandatory_settings) as new_context:
            pass


async def test_never_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        never_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.NEVER)
        with pytest.raises(exceptions.PropagationNeverTrmException):
            async with transaction_manager.do(new_context, settings=never_settings) as new_context2:
                pass


async def test_not_supported_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        not_supported_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.NOT_SUPPORTED)
        async with transaction_manager.do(new_context, settings=not_supported_settings) as new_context2:
            assert new_context2.find(settings.key) is None


async def test_requires_new_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        requires_new_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.REQUIRES_NEW)
        async with transaction_manager.do(new_context, settings=requires_new_settings) as new_context2:
            assert new_context2.find(settings.key) is not new_context.find(settings.key)


async def test_supports_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    supports_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.SUPPORTS)
    async with transaction_manager.do(context, settings=supports_settings) as new_context:
        assert new_context.find(settings.key) is None


def _get_session(context: contexts.Context, settings: pytrm.UniqSettings, reg: pytrm.Registry) -> AsyncSession:
    session = pytrm.get_native_transaction(context, settings.id, reg=reg)
    if not isinstance(session, AsyncSession):
        raise ValueError("wrong sqlalchemy session")

    return session
