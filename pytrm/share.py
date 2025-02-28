import enum
import sys
from typing import (
    Any,
    AsyncContextManager,
    Final,
    Hashable,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    runtime_checkable,
)

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

    def find(self, key: ContextKey) -> Optional[ContextValue]:
        """Найти значение по ключу"""

    def set(self, key: ContextKey, value: ContextValue) -> Self:
        """Задать значение по ключу"""

    def remove(self, key: ContextKey) -> Self:
        """Удалить значение по ключу"""


class Key:
    """Ключ, по которому в хранилище помещаются и достаются транзакции"""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented

        return self._value == value._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._value)


class Propagation(enum.IntEnum):
    """Правила распространения транзакции"""

    # Поддерживает текущую транзакцию, создает новую если ее не существует
    REQUIRED = enum.auto()

    # Выполняет во вложенной транзакции
    NESTED = enum.auto()

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

    id: SettingsID  # Идентификатор
    key: Key  # Ключ для сохранения транзакции в контекст
    propagation: Propagation  # Правила распространения транзакции

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Settings):
            return NotImplemented

        return self.id == value.id

    def __hash__(self) -> int:
        return hash(self.id)


class SettingsStorage:
    """Хранилище настроек"""

    def __init__(self, data: Mapping[SettingsID, Settings]) -> None:
        self._data = data

    @classmethod
    def create(cls, settings: Iterable[Settings]) -> Self:
        data = dict((s.id, s) for s in settings)
        if not data:
            raise exceptions.NoSettingsException

        return cls(data)

    def get(self, id_: SettingsID) -> Settings:
        if (settings := self._data.get(id_)) is None:
            raise exceptions.SettingsNotFoundException

        return settings


class ContextManager:
    """Базовая реализация контекстного менеджера"""

    __slots__ = ()

    def get(self, ctx: Context, key: Key) -> Transaction:
        """
        Получить транзакцию

        :param ctx: контекст
        :param key: ключ
        :return: транзакция
        :raises TransactionNotFoundInContextException: если транзакция не найдена
        :raises UnknownValueInContextException: если найденное значение не является транзакцией
        """
        transaction = ctx.find(key)
        if transaction is None:
            raise exceptions.TransactionNotFoundInContextException

        if not isinstance(transaction, Transaction):
            raise exceptions.UnknownValueInContextException

        return transaction

    def set(
        self,
        ctx: Context,
        key: Key,
        transaction: Transaction,
    ) -> Context:
        """
        Задать значение

        :param ctx: контекст
        :param key: ключ
        :param transaction: транзакция
        :return: контекст
        """
        return ctx.set(key, transaction)

    def remove(
        self,
        ctx: Context,
        key: Key,
    ) -> Context:
        """
        Удалить значение

        :param ctx: контекст
        :param key: ключ
        :return: контекст
        """
        return ctx.remove(key)


DEFAULT_CONTEXT_MANAGER: Final = ContextManager()


ContextT = TypeVar("ContextT", bound=Context)


class TransactionManager(Protocol[ContextT]):
    """Менеджер транзакций"""

    def do(
        self,
        ctx: ContextT,
        *,
        settings: Optional[Settings] = None,
        exclude: Tuple[Type[BaseException], ...] = (),
    ) -> AsyncContextManager[ContextT]:
        """
        Выполнить в транзакции

        :param ctx: контекст
        :param settings: настройки (если не указаны, то используются настройки по умолчанию)
        :param exclude: типы исключений, при которых требуется делать фиксацию изменений, вместа отката
        :return: новый контекст в асинхронном контекстном менеджере Python Core
        :raises BaseTrmException: если произошла какая-либо ошибка
        """


class _RegistryData(NamedTuple):
    """Данные реестра"""

    # Хранилище настроек
    settings_storage: SettingsStorage

    # Менеджер контекста
    ctx_manager: ContextManager

    # Имя атрибута, содержащего менеджер транзакций
    trm_attr_name: Optional[str]

    # Имя атрибута, содержащего настройки менеджера транзакций
    trm_settings_attr_name: Optional[str]


class Registry:
    """Реестр"""

    __slots__ = ("_data",)

    _data: Optional[_RegistryData]

    def __init__(self) -> None:
        self._data = None

    def initialize(
        self,
        settings_storage: SettingsStorage,
        ctx_manager: ContextManager,
        trm_attr_name: Optional[str],
        trm_settings_attr_name: Optional[str],
    ) -> None:
        """
        Инициализировать реестр

        :param default_settings: настройки по умолчанию
        :param settings_storage: хранилище настроек
        :param ctx_manager: менеджер контекста
        :param transaction_manager_attr_name: имя атрибута, содержащего менеджер транзакций
        :param transaction_manager_settings_attr_name: имя атрибута, содержащего настройки менеджера транзакций
        :return: None
        :raises RegistryIsAlreadyInitializedException: если реестр уже инициализирован
        """
        if self._data is not None:
            raise exceptions.RegistryIsAlreadyInitializedException

        self._data = _RegistryData(
            settings_storage=settings_storage,
            ctx_manager=ctx_manager,
            trm_attr_name=trm_attr_name,
            trm_settings_attr_name=trm_settings_attr_name,
        )

    def get_settings_by_id(self, id_: SettingsID) -> Settings:
        """
        Получить настройки по идентификатору

        :param id_: идентификатор настроек
        :return: настройки по умолчанию
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        :raises SettingsNotFoundException: если настройки не найдены
        """
        data = self._get_registry_data()
        settings = data.settings_storage.get(id_)
        return settings

    def get_ctx_manager(self) -> ContextManager:
        """
        Получить контекстный менеджер

        :return: настройки по умолчанию
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        """
        data = self._get_registry_data()
        return data.ctx_manager

    def get_trm_attr_name(self) -> str:
        """
        Получить имя атрибута, содержащего менеджер транзакций

        :return: имя атрибута, содержащего менеджер транзакций
        :raises TrmAttrNameNoAtRegistryException: если реестр не инициализирован
        """
        data = self._get_registry_data()
        if data.trm_attr_name is None:
            raise exceptions.TrmAttrNameNoAtRegistryException

        return data.trm_attr_name

    def get_trm_settings_attr_name(self) -> str:
        """
        Получить имя атрибута, содержащего настройки менеджера транзакций

        :return: имя атрибута, содержащего менеджер транзакций
        :raises TrmSettingsAttrNameNoAtRegistryException: если реестр не инициализирован
        """
        data = self._get_registry_data()
        if data.trm_settings_attr_name is None:
            raise exceptions.TrmSettingsAttrNameNoAtRegistryException

        return data.trm_settings_attr_name

    def _get_registry_data(self) -> _RegistryData:
        if self._data is None:
            raise exceptions.RegistryIsNotInitializedException

        return self._data


DEFAULT_REGISTRY: Final = Registry()


def get_native_transaction(
    ctx: Context,
    settings_id: SettingsID,
    *,
    reg: Registry = DEFAULT_REGISTRY,
) -> Tr:
    """
    Получить нативную транзакцию

    :param ctx: контекст
    :param settings_id: ID настроек
    :param reg: реестр
    :return: нативная транзакция
    :raises RegistryIsNotInitializedException: если реестр не инициализирован
    :raises SettingsNotFoundException: если настройки не найдены
    :raises TransactionNotFoundInContextException: если транзакция не найдена
    :raises UnknownValueInContextException: если найденное значение не является транзакцией
    """
    settings = reg.get_settings_by_id(settings_id)
    ctx_manager = reg.get_ctx_manager()
    key = settings.key

    transaction = ctx_manager.get(ctx, key)
    return transaction.unwrap()
