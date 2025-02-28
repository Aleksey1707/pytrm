"""
PyTRM is a transaction manager as abstraction of database access.
"""

from . import exceptions, impls
from .configurations import configurate, get_configurated_reg
from .decorators import transactional, transactional_with
from .share import (
    Context,
    ContextManager,
    Key,
    NativeTransaction,
    Propagation,
    Registry,
    Settings,
    SettingsID,
    Transaction,
    TransactionManager,
    find_native_transaction,
    get_native_transaction,
)

__version__ = "0.1.0"
__date__ = "2024-12-31"
__author__ = "Aleksey Odinokov"
__license__ = "MIT"
