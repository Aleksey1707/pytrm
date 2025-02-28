from typing import AsyncIterator, Final, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

import pytrm
from pytrm.impls import sqlalchemy as trm

pytestmark = pytest.mark.asyncio

metadata: Final = MetaData()

test_table: Final = Table(
    "test",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("value", Integer, nullable=False),
)


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer(
        "postgres:16-alpine",
        username="test",
        password="test",
        dbname="test",
        driver="asyncpg",
    ) as container:
        yield container


@pytest_asyncio.fixture(scope="session")
async def system_engine(
    postgres: PostgresContainer,
) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        url=postgres.get_connection_url(),
        isolation_level="AUTOCOMMIT",
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def engine(
    postgres: PostgresContainer,
) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(url=postgres.get_connection_url())
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def setup(
    system_engine: AsyncEngine,
) -> AsyncIterator[None]:
    async with system_engine.connect() as conn:
        await conn.run_sync(metadata.create_all)

    yield

    async with system_engine.connect() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture(scope="session")
def sessionmaker_(
    engine: AsyncEngine,
) -> sessionmaker:
    return sessionmaker(  # type: ignore[call-overload]
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


@pytest.fixture(scope="session")
def transaction_manager(
    setup: None,
    sessionmaker_: sessionmaker,
    settings: pytrm.Settings,
    registry: pytrm.Registry,
) -> pytrm.TransactionManager:
    transaction_manager = trm.SqlAlchemyTransactionManager.create(sessionmaker_, settings.id, reg=registry)
    return transaction_manager
