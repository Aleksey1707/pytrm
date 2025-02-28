import pytest
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

import pytrm
from pytrm.impls.mongo import motor as trm
from tests.mongo.conftest import CustomDockerContainer
from tests.mongo.motor.repositories import MotorMongoRepository


@pytest.fixture(scope="session")
def mongo_client(mongo: CustomDockerContainer) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(mongo.connection_url)


@pytest.fixture(scope="session")
def mongo_db(mongo_client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    return mongo_client["testdb"]


@pytest.fixture(scope="session")
def transaction_manager(
    mongo_client: AsyncIOMotorClient,
    settings: pytrm.Settings,
    registry: pytrm.Registry,
) -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = trm.MongoTransactionManager.create(mongo_client, settings.id, reg=registry)
    return transaction_manager


@pytest.fixture(scope="session")
def repository(
    mongo_db: AsyncIOMotorDatabase,
    settings: pytrm.Settings,
    registry: pytrm.Registry,
) -> MotorMongoRepository:
    collection = mongo_db["test"]
    repository = MotorMongoRepository(collection=collection, settings_id=settings.id, reg=registry)
    return repository
