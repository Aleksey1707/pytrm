"""
PyTRM is a transaction manager as abstraction of database access.
"""

from .configurations import configurate as configurate
from .configurations import get_configurated_reg as get_configurated_reg
from .decorators import transactional as transactional
from .decorators import transactional_with as transactional_with
from .share import Context as Context
from .share import ContextManager as ContextManager
from .share import Key as Key
from .share import NativeTransaction as NativeTransaction
from .share import Propagation as Propagation
from .share import Registry as Registry
from .share import Settings as Settings
from .share import SettingsID as SettingsID
from .share import SettingsStorage as SettingsStorage
from .share import Transaction as Transaction
from .share import TransactionManager as TransactionManager
from .share import find_native_transaction as find_native_transaction
from .share import get_native_transaction as get_native_transaction

__version__ = "0.2.1"
__date__ = "2025-08-17"
__author__ = "Aleksey Odinokov"
__license__ = "MIT"
