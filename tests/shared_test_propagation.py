import dataclasses

import pytest

import pytrm
from pytrm import exceptions
from tests import contexts

pytestmark = pytest.mark.asyncio


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
