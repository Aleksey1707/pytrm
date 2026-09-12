import dataclasses
from typing import Final

import pytest
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis.exceptions import ResponseError

import pytrm
from pytrm import exceptions
from tests import contexts
from tests.shared_test_propagation import test_mandatory_propagation as test_mandatory_propagation
from tests.shared_test_propagation import test_never_propagation as test_never_propagation
from tests.shared_test_propagation import test_not_supported_propagation as test_not_supported_propagation
from tests.shared_test_propagation import test_requires_new_propagation as test_requires_new_propagation
from tests.shared_test_propagation import test_supports_propagation as test_supports_propagation

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


async def test_nested_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        nested_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.NESTED)
        with pytest.raises(exceptions.NestedTransactionsNotSupportedTrmException):
            async with transaction_manager.do(new_context, settings=nested_settings):
                pass


async def test_required_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    registry: pytrm.Registry,
    redis_client: Redis,
) -> None:
    # given: ключ для записи, транзакции ещё нет
    KEY: Final = "pytrm:test:required"
    VALUE: Final = "value"
    required_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.REQUIRED)
    assert context.find(required_settings.key) is None
    await redis_client.delete(KEY)

    # when: накапливаем SET в pipeline внутри транзакции
    async with transaction_manager.do(context) as new_context:
        assert new_context.find(required_settings.key) is not None
        pipe = _get_pipeline(new_context, settings, registry)
        pipe.set(KEY, VALUE)
        assert await redis_client.get(KEY) is None

    # then: после commit значение видно обычным клиентом
    assert await redis_client.get(KEY) == VALUE
    assert context.find(required_settings.key) is None
    await redis_client.delete(KEY)


async def test_rollback_discards_buffered_commands(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    registry: pytrm.Registry,
    redis_client: Redis,
) -> None:
    # given
    KEY: Final = "pytrm:test:rollback"
    await redis_client.delete(KEY)

    # when: накапливаем команду и прерываем блок исключением
    with pytest.raises(RuntimeError, match="need rollback"):
        async with transaction_manager.do(context) as new_context:
            pipe = _get_pipeline(new_context, settings, registry)
            pipe.set(KEY, "value")
            raise RuntimeError("need rollback")

    # then: команда не была отправлена на сервер
    assert await redis_client.get(KEY) is None


async def test_exec_applies_valid_commands_despite_later_error_in_batch(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    registry: pytrm.Registry,
    redis_client: Redis,
) -> None:
    """Канарейка: документирует поведение Redis MULTI/EXEC, а не баг реализации.

    При ошибке одной команды в пакете остальные команды всё равно применяются на сервере.
    """
    # given
    VALID_KEY: Final = "pytrm:test:canary:valid"
    WRONGTYPE_KEY: Final = "pytrm:test:canary:wrongtype"
    await redis_client.delete(VALID_KEY, WRONGTYPE_KEY)
    await redis_client.set(WRONGTYPE_KEY, "string-value")

    # when
    with pytest.raises(ResponseError):
        async with transaction_manager.do(context) as new_context:
            pipe = _get_pipeline(new_context, settings, registry)
            pipe.set(VALID_KEY, "applied")
            pipe.lpush(WRONGTYPE_KEY, "item")

    # then: валидная команда применена, несмотря на ошибку соседней
    assert await redis_client.get(VALID_KEY) == "applied"
    await redis_client.delete(VALID_KEY, WRONGTYPE_KEY)


def _get_pipeline(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    reg: pytrm.Registry,
) -> Pipeline:
    native = pytrm.get_native_transaction(context, settings.id, reg=reg)
    if not isinstance(native, Pipeline):
        raise ValueError("wrong redis pipeline")

    return native
