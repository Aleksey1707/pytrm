import pytest

import pytrm
from tests import contexts

pytestmark = pytest.mark.asyncio


async def test_null_trm(
    context: contexts.Context,
    transaction_manager: pytrm.TransactionManager,
) -> None:
    async with transaction_manager.do(context) as new_context:
        assert new_context is not context
