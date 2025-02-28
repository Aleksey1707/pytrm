import pytest

import pytrm
from pytrm import null as trm


@pytest.fixture(scope="session")
def transaction_manager() -> pytrm.TransactionManager:
    transaction_manager: pytrm.TransactionManager
    transaction_manager = trm.NullTransactionManager()
    return transaction_manager
