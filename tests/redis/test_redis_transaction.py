from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio.client import Pipeline

from pytrm.impls.redis import RedisTransaction


@pytest.fixture
def pipeline() -> MagicMock:
    mock = MagicMock(spec=Pipeline)
    mock.execute = AsyncMock()
    mock.reset = AsyncMock()
    return mock


@pytest.fixture
def transaction(pipeline: MagicMock) -> RedisTransaction:
    return RedisTransaction(pipeline)


@pytest.mark.asyncio
async def test_is_active_before_begin(transaction: RedisTransaction) -> None:
    assert transaction.is_active() is False


@pytest.mark.asyncio
async def test_begin_sets_active(transaction: RedisTransaction) -> None:
    # when
    await transaction.begin()

    # then
    assert transaction.is_active() is True


@pytest.mark.asyncio
async def test_commit_calls_execute_and_deactivates(
    transaction: RedisTransaction,
    pipeline: MagicMock,
) -> None:
    # given
    await transaction.begin()

    # when
    await transaction.commit()

    # then
    pipeline.execute.assert_awaited_once()
    assert transaction.is_active() is False


@pytest.mark.asyncio
async def test_commit_deactivates_on_execute_error(
    transaction: RedisTransaction,
    pipeline: MagicMock,
) -> None:
    # given
    await transaction.begin()
    pipeline.execute.side_effect = RuntimeError("execute failed")

    # when
    with pytest.raises(RuntimeError, match="execute failed"):
        await transaction.commit()

    # then
    assert transaction.is_active() is False


@pytest.mark.asyncio
async def test_rollback_calls_reset_not_execute(
    transaction: RedisTransaction,
    pipeline: MagicMock,
) -> None:
    # given
    await transaction.begin()

    # when
    await transaction.rollback()

    # then
    pipeline.reset.assert_awaited_once()
    pipeline.execute.assert_not_awaited()
    assert transaction.is_active() is False


@pytest.mark.asyncio
async def test_rollback_deactivates_on_reset_error(
    transaction: RedisTransaction,
    pipeline: MagicMock,
) -> None:
    # given
    await transaction.begin()
    pipeline.reset.side_effect = RuntimeError("reset failed")

    # when
    with pytest.raises(RuntimeError, match="reset failed"):
        await transaction.rollback()

    # then
    assert transaction.is_active() is False


def test_unwrap_returns_pipeline(
    transaction: RedisTransaction,
    pipeline: MagicMock,
) -> None:
    assert transaction.unwrap() is pipeline
