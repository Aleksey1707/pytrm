import enum
import sys
from typing import Any, AsyncContextManager, Hashable, Mapping, NamedTuple, Optional, Protocol, runtime_checkable

from pytrm import exceptions

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

Tr: TypeAlias = Any
SettingsID: TypeAlias = Hashable


ContextKey: TypeAlias = Hashable
ContextValue: TypeAlias = Any


class Context(Protocol):
    """Контекст (immutable)"""

    def get(self, key: ContextKey) -> ContextValue:
        """Получить значение по ключу"""

    def set(self, key: ContextKey, value: ContextValue) -> Self:
        """Задать значение по ключу"""


class Key:
    """Ключ, по которому в хранилище помещаются и достаются транзакции"""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value


class Propagation(enum.IntEnum):
    """Правила распространения транзакции"""

    # Поддерживает текущую транзакцию, создает новую если ее не существует
    REQUIRED = enum.auto()

    # Поддерживает текущую транзакцию.
    # Генерирует исключение, если таковая не существует.
    MANDATORY = enum.auto()

    # Выполняется не транзакционно. Генерирует исключение, если транзакция существует.
    NEVER = enum.auto()

    # Выполняется без транзакции. Приостанавливает текущую транзакцию, если она существует.
    NOT_SUPPORTED = enum.auto()

    # Создает новую транзакцию, приостанавливает текущую транзакцию, если она существует.
    REQUIRES_NEW = enum.auto()

    # Поддерживает текущую транзакцию. Выполняется не транзакционно, если таковая не существует.
    SUPPORTS = enum.auto()


@runtime_checkable
class Transaction(Protocol):
    """Абстракция над транзакцией"""

    def is_active(self) -> bool:
        """Является ли транзакция активной"""

    async def begin(self) -> None:
        """Начать транзакцию"""

    async def commit(self) -> None:
        """Зафиксировать транзакцию"""

    async def rollback(self) -> None:
        """Откатить транзакцию"""

    def unwrap(self) -> Tr:
        """Распаковать (получить нативную транзакцию)"""


class Settings(NamedTuple):
    """Настройки"""

    key: Key  # ключ для сохранения транзакции в контекст
    propagation: Propagation  # правила распространения транзакции


class SettingsStorage:
    """Хранилище настроек"""

    def __init__(self, data: Mapping[SettingsID, Settings]) -> None:
        self._data = data

    def get(self, id_: SettingsID) -> Settings:
        if (settings := self._data.get(id_)) is None:
            raise exceptions.SettingsNotFoundException

        return settings


class ContextManager(Protocol):
    """
    Интерфейс менеджера контекста

    Получение и сохранение транзакций в контекст должно происходить только через реализации менеджера контекста
    """

    def get_default(self, ctx: Context) -> Transaction: ...

    def set_default(self, ctx: Context, transaction: Transaction) -> Context: ...

    def get_by_key(self, ctx: Context, key: Key) -> Transaction: ...

    def set_by_key(self, ctx: Context, key: Key, transaction: Transaction) -> Context: ...


class TransactionManager(Protocol):

    def do(
        self,
        ctx: Context,
        settings: Optional[Settings] = None,
    ) -> AsyncContextManager[None]:
        """Выполнить в транзакции"""
