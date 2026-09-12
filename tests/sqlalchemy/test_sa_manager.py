from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import pytrm
from pytrm.impls import sqlalchemy as trm

pytestmark = pytest.mark.asyncio

FIRST_URL = "postgresql+asyncpg://user:pass@localhost/first"
SECOND_URL = "postgresql+asyncpg://user:pass@localhost/second"


async def test_each_manager_uses_its_own_sessionmaker(
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> None:
    # given: два менеджера с разными фабриками сессий
    first_engine = create_async_engine(FIRST_URL)
    second_engine = create_async_engine(SECOND_URL)
    first_manager = _manager(first_engine, settings, registry)
    second_manager = _manager(second_engine, settings, registry)

    # when: каждый создаёт транзакцию
    first_transaction = await first_manager._create_transaction()
    second_transaction = await second_manager._create_transaction()

    # then: сессии привязаны к своим движкам, а не к движку первого менеджера
    assert first_transaction.unwrap().get_bind() is first_engine.sync_engine
    assert second_transaction.unwrap().get_bind() is second_engine.sync_engine

    await first_engine.dispose()
    await second_engine.dispose()


async def test_commit_closes_session(
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> None:
    # given: транзакция поверх сессии, которая запоминает вызов close
    engine = create_async_engine(FIRST_URL)
    manager = _manager(engine, settings, registry, session_class=TrackingSession)
    transaction = await manager._create_transaction()
    session = transaction.unwrap()
    assert session.is_closed is False

    # when: фиксация
    await transaction.commit()

    # then: сессия закрыта
    assert session.is_closed is True

    await engine.dispose()


async def test_rollback_closes_session(
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> None:
    engine = create_async_engine(FIRST_URL)
    manager = _manager(engine, settings, registry, session_class=TrackingSession)
    transaction = await manager._create_transaction()
    session = transaction.unwrap()

    await transaction.rollback()

    assert session.is_closed is True

    await engine.dispose()


class TrackingSession(AsyncSession):
    """Сессия, которая запоминает, что её закрыли"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.is_closed = False

    async def close(self) -> None:
        self.is_closed = True
        await super().close()


def _manager(
    engine: Any,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
    session_class: Any = AsyncSession,
) -> trm.SqlAlchemyTransactionManager:
    maker = sessionmaker(engine, expire_on_commit=False, class_=session_class)
    return trm.SqlAlchemyTransactionManager.create(maker, settings.id, reg=registry)
