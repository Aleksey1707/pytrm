import abc
from typing import ClassVar, Optional


class BaseTrmException(Exception, metaclass=abc.ABCMeta):
    default_message: ClassVar[Optional[str]] = None

    def __init__(self, *args: object) -> None:
        if args or self.default_message is None:
            super().__init__(*args)
        else:
            super().__init__(self.default_message)


# =============================================================================
# Context manger
# =============================================================================


class BaseContextManagerTrmException(BaseTrmException, metaclass=abc.ABCMeta):
    """Базовое исключение контекстноо менеджера транзакций"""


class TransactionNotFoundInContextException(BaseContextManagerTrmException):
    default_message = "В контексте отсутствует транзакция"


class UnknownValueInContextException(BaseContextManagerTrmException):
    default_message = "В контексте оказалось значение неверного типа"


# =============================================================================
# Propagation
# =============================================================================


class BasePropagationTrmException(BaseTrmException, metaclass=abc.ABCMeta):
    """Базовое исключение распространения транзакции"""


class PropagationMandatoryTrmException(BasePropagationTrmException):
    default_message = "Нет действующей транзакции"


class PropagationNeverTrmException(BasePropagationTrmException):
    default_message = "Обнаружена транзакция, которой не должно быть."


# =============================================================================
# Transaction
# =============================================================================


class BaseTransactionTrmException(BaseTrmException, metaclass=abc.ABCMeta):
    """Базовое исключение транзакции"""


class CriticalTransactionTrmException(BaseTransactionTrmException):
    default_message = "Ошибка при работе с транзакцией"


class TransactionAlreadyClosedTrmException(BaseTransactionTrmException):
    default_message = "Транзакция уже закрыта"


class TransactionStartTrmException(BaseTransactionTrmException):
    default_message = "Ошибка при старте транзакции"


class TransactionCommitTrmException(BaseTransactionTrmException):
    default_message = "Ошибка при завершении транзакции"


class TransactionRollbackTrmException(BaseTransactionTrmException):
    default_message = "Ошибка при откате транзакции"


# =============================================================================
# Registry
# =============================================================================


class BaseRegistryTrmException(BaseTrmException, metaclass=abc.ABCMeta):
    """Базовое исключение реестра"""


class RegistryIsNotInitializedException(BaseRegistryTrmException):
    default_message = "Реестр не инициализирован"


class RegistryIsAlreadyInitializedException(BaseRegistryTrmException):
    default_message = "Реестр уже инициализирован"


# =============================================================================
# Settings
# =============================================================================


class BaseSettingsTrmException(BaseTrmException, metaclass=abc.ABCMeta):
    """Базовое исключение настроек"""


class SettingsNotFoundException(BaseSettingsTrmException):
    default_message = "Настройки не найдены"
