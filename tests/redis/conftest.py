from typing import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from testcontainers.redis import RedisContainer

import pytrm
from pytrm.impls import redis as trm


@pytest.fixture(scope="session")
def redis_container() -> Iterator[RedisContainer]:
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest_asyncio.fixture(scope="session")
async def redis_client(redis_container: RedisContainer) -> AsyncIterator[Redis]:
    client = Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(redis_container.port),
        password=redis_container.password,
        decode_responses=True,
    )
    yield client
    await client.aclose()


@pytest.fixture(scope="session")
def transaction_manager(
    redis_client: Redis,
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> pytrm.TransactionManager:
    return trm.RedisTransactionManager.create(redis_client, settings.id, reg=registry)
