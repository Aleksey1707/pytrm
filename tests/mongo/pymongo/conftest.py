import asyncio
from collections.abc import AsyncIterator
from typing import Any, Dict

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

import pytrm
from pytrm.impls.mongo import pymongo as trm
from tests.mongo.conftest import CustomDockerContainer
from tests.mongo.pymongo.repositories import PymongoMongoRepository


@pytest_asyncio.fixture(scope="session")
async def mongo_client(mongo: CustomDockerContainer) -> AsyncIterator[AsyncMongoClient[Dict[str, Any]]]:
    client = AsyncMongoClient[Dict[str, Any]](mongo.connection_url)
    yield client
    await client.close()
    await asyncio.sleep(0.5)


@pytest.fixture(scope="session")
def mongo_db(mongo_client: AsyncMongoClient) -> AsyncDatabase:
    return mongo_client["testdb"]


@pytest.fixture(scope="session")
def transaction_manager(
    mongo_client: AsyncMongoClient,
    settings: pytrm.Settings,
    registry: pytrm.Registry,
) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = trm.MongoTransactionManager.create(mongo_client, settings.id, reg=registry)
    return transaction_manager


@pytest.fixture(scope="session")
def repository(
    mongo_db: AsyncDatabase,
    settings: pytrm.Settings,
    registry: pytrm.Registry,
) -> PymongoMongoRepository:
    collection = mongo_db["test"]
    repository = PymongoMongoRepository(collection=collection, settings_id=settings.id, reg=registry)
    return repository
