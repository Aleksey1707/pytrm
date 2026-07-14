import sys
from typing import Any, Dict, Optional

from motor.core import AgnosticClient, AgnosticClientSession

from pytrm import bases, exceptions, share

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

MongoSessionData = Dict[str, Any]
MongoTransactionData = Dict[str, Any]

MongoClient = AgnosticClient
MongoSession = AgnosticClientSession


class MongoTransaction:
    """Обертка над транзакцией MongoDB"""

    __slots__ = ("_session", "_transaction_data")

    def __init__(
        self,
        session: MongoSession,
        transaction_data: Optional[MongoTransactionData] = None,
    ) -> None:
        self._session = session
        self._transaction_data = transaction_data

    @classmethod
    async def create(
        cls,
        client: MongoClient,
        session_data: Optional[MongoSessionData] = None,
        transaction_data: Optional[MongoTransactionData] = None,
    ) -> Self:
        """
        Создать транзакцию MongoDB

        :param client: клиент MongoDB
        :param session_data: параметры сессии
        :param transaction_data: параметры транзакции
        :return: экземпляр транзакции
        """
        if session_data is None:
            session_data = dict()

        session = await client.start_session(**session_data)
        return cls(session, transaction_data)

    def is_active(self) -> bool:
        """
        Проверить, активна ли транзакция

        :return: True, если транзакция активна
        """
        return self._session.in_transaction  # type: ignore

    async def begin(self) -> None:
        """Начать транзакцию"""
        if self._transaction_data is None:
            transaction_data = {}
        else:
            transaction_data = self._transaction_data

        self._session.start_transaction(**transaction_data)

    async def commit(self) -> None:
        """Зафиксировать транзакцию"""
        await self._session.commit_transaction()
        await self._session.end_session()

    async def rollback(self) -> None:
        """Откатить транзакцию"""
        await self._session.abort_transaction()
        await self._session.end_session()

    def unwrap(self) -> share.NativeTransaction:
        """
        Получить нативную сессию MongoDB

        :return: сессия MongoDB
        """
        return self._session


class MongoTransactionManager(bases.BaseTransactionManager):
    """Менджер транзакций MongoDB"""

    __slots__ = ("_client", "_session_data", "_transaction_data")

    def __init__(
        self,
        ctx_manager: share.ContextManager,
        settings: share.UniqSettings,
        client: MongoClient,
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
        client: MongoClient,
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

    async def _create_transaction(self) -> share.Transaction:
        if self._session_data is None:
            session_data = {}
        else:
            session_data = self._session_data

        session = await self._client.start_session(**session_data)
        return MongoTransaction(
            session=session,
            transaction_data=self._transaction_data,
        )

    async def _create_nested_transaction(self) -> share.Transaction:
        raise exceptions.NestedTransactionsNotSupportedTrmException
