import abc
import sys
from typing import Any, Dict, Generic, Optional, Protocol, TypeVar

from pytrm import bases, exceptions, share

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

MongoSessionData = Dict[str, Any]
MongoTransactionData = Dict[str, Any]


class MongoSession(Protocol):
    """Сессия MongoDB в объёме, который нужен обёртке над транзакцией"""

    @property
    def in_transaction(self) -> bool:
        """Открыта ли транзакция в сессии"""

    async def commit_transaction(self) -> None:
        """Зафиксировать транзакцию"""

    async def abort_transaction(self) -> None:
        """Откатить транзакцию"""

    async def end_session(self) -> None:
        """Завершить сессию"""


ClientT = TypeVar("ClientT")


class BaseMongoTransaction(abc.ABC):
    """Базовая обёртка над транзакцией MongoDB"""

    __slots__ = ("_session", "_transaction_data")

    def __init__(
        self,
        session: MongoSession,
        transaction_data: Optional[MongoTransactionData] = None,
    ) -> None:
        self._session = session
        self._transaction_data = transaction_data

    def is_active(self) -> bool:
        """
        Проверить, активна ли транзакция

        :return: True, если транзакция активна
        """
        return self._session.in_transaction

    async def begin(self) -> None:
        """Начать транзакцию"""
        await self._start_transaction(self._transaction_data or {})

    async def commit(self) -> None:
        """Зафиксировать транзакцию и завершить сессию"""
        try:
            await self._session.commit_transaction()
        finally:
            await self._session.end_session()

    async def rollback(self) -> None:
        """Откатить транзакцию и завершить сессию"""
        try:
            await self._session.abort_transaction()
        finally:
            await self._session.end_session()

    def unwrap(self) -> share.NativeTransaction:
        """
        Получить нативную сессию MongoDB

        :return: сессия MongoDB
        """
        return self._session

    @abc.abstractmethod
    async def _start_transaction(self, transaction_data: MongoTransactionData) -> None: ...


class BaseMongoTransactionManager(bases.BaseTransactionManager, Generic[ClientT]):
    """Базовый менеджер транзакций MongoDB"""

    __slots__ = ("_client", "_session_data", "_transaction_data")

    def __init__(
        self,
        ctx_manager: share.ContextManager,
        settings: share.UniqSettings,
        client: ClientT,
        session_data: Optional[MongoSessionData],
        transaction_data: Optional[MongoTransactionData],
    ) -> None:
        super().__init__(ctx_manager, settings)
        self._client = client
        self._session_data = session_data
        self._transaction_data = transaction_data

    @classmethod
    def create(
        cls,
        client: ClientT,
        settings_id: share.SettingsID,
        session_data: Optional[MongoSessionData] = None,
        transaction_data: Optional[MongoTransactionData] = None,
        *,
        reg: share.Registry = share.DEFAULT_REGISTRY,
    ) -> Self:
        """
        Создать менеджер транзакций MongoDB

        :param client: клиент MongoDB
        :param settings_id: идентификатор настроек
        :param session_data: параметры сессии
        :param transaction_data: параметры транзакции
        :param reg: реестр
        :return: менеджер транзакций
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        :raises SettingsNotFoundException: если настройки не найдены
        """
        ctx_manager = reg.get_ctx_manager()
        settings = reg.get_settings_by_id(settings_id)

        return cls(
            client=client,
            ctx_manager=ctx_manager,
            settings=settings,
            session_data=session_data,
            transaction_data=transaction_data,
        )

    async def _create_nested_transaction(self, transaction: share.Transaction) -> share.Transaction:
        raise exceptions.NestedTransactionsNotSupportedTrmException

    def _session_kwargs(self) -> MongoSessionData:
        return self._session_data or {}
