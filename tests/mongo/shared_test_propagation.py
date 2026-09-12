import dataclasses

import bson
import pytest

import pytrm
from pytrm import exceptions
from tests import contexts
from tests.mongo.base_repos import BaseMongoRepository
from tests.repositories import EntityNotFoundRepositoryException

pytestmark = pytest.mark.asyncio


async def test_required_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
    repository: BaseMongoRepository,
) -> None:
    # given: данные для сохранения, транзакции ещё нет
    required_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.REQUIRED)
    _id = bson.ObjectId()
    data = dict(
        _id=_id,
        a="a",
        b=1,
        c=True,
    )
    assert context.find(required_settings.key) is None

    # when: сохраняем сущность в транзакции
    async with transaction_manager.do(context) as new_context:
        assert new_context.find(required_settings.key) is not None
        await repository.save(data, context=new_context)

    # then: сущность читается как во внешней, так и во вложенной транзакции
    async with transaction_manager.do(context) as new_context:
        db_data = await repository.get(_id, context=new_context)
        assert db_data == data

        async with transaction_manager.do(new_context) as new_context2:
            db_data = await repository.get(_id, context=new_context2)
            assert db_data == data

        # and: удаляем сущность в той же транзакции
        await repository.delete(_id, context=new_context)

    # then: после удаления сущность больше не найти
    async with transaction_manager.do(context) as new_context:
        with pytest.raises(EntityNotFoundRepositoryException):
            await repository.get(_id, context=new_context)

    assert context.find(required_settings.key) is None


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


async def test_mandatory_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    mandatory_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.MANDATORY)

    with pytest.raises(exceptions.PropagationMandatoryTrmException):
        async with transaction_manager.do(context, settings=mandatory_settings):
            pass


async def test_never_propagation(
    context: contexts.Context,
    settings: pytrm.UniqSettings,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        never_settings = dataclasses.replace(settings, propagation=pytrm.Propagation.NEVER)
        with pytest.raises(exceptions.PropagationNeverTrmException):
            async with transaction_manager.do(new_context, settings=never_settings):
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
