import abc
import sys
from typing import ClassVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from pytrm import bases, share

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


class BaseSqlAlchemyTransaction(abc.ABC):
    """Базовая обёртка над транзакцией SqlAlchemy"""

    _sessionmaker: ClassVar[Optional[sessionmaker]] = None

    __slots__ = ("_session",)

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    @classmethod
    def create(
        cls,
        sessionmaker: sessionmaker,
    ) -> Self:
        """
        Создать транзакцию

        :param sessionmaker: фабрика сессий SqlAlchemy
        :return: экземпляр транзакции
        """
        if cls._sessionmaker is None:
            cls._sessionmaker = sessionmaker

        session = cls._sessionmaker()
        return cls(session)

    def is_active(self) -> bool:
        """
        Проверить, активна ли транзакция

        :return: True, если транзакция активна
        """
        return self._session.in_transaction()

    @abc.abstractmethod
    async def begin(self) -> None:
        """Начать транзакцию"""

    async def commit(self) -> None:
        """Зафиксировать транзакцию"""
        await self._session.commit()

    async def rollback(self) -> None:
        """Откатить транзакцию"""
        await self._session.rollback()

    def unwrap(self) -> share.NativeTransaction:
        """
        Получить нативную сессию SqlAlchemy

        :return: сессия SqlAlchemy
        """
        return self._session


class SqlAlchemyTransaction(BaseSqlAlchemyTransaction):
    """Обертка над транзакцией SqlAlchemy"""

    async def begin(self) -> None:
        """Начать транзакцию"""
        await self._session.begin()


class SqlAlchemyNestedTransaction(BaseSqlAlchemyTransaction):
    """Обертка над вложенной транзакцией SqlAlchemy"""

    async def begin(self) -> None:
        """Начать вложенную транзакцию"""
        await self._session.begin_nested()


class SqlAlchemyTransactionManager(bases.BaseTransactionManager):
    """Менджер транзакций SqlAlchemy"""

    __slots__ = ("_sessionmaker",)

    def __init__(
        self,
        ctx_manager: share.ContextManager,
        settings: share.UniqSettings,
        sessionmaker_: sessionmaker,
    ) -> None:
        super().__init__(ctx_manager, settings)
        self._sessionmaker = sessionmaker_

    @classmethod
    def create(
        cls,
        sessionmaker_: sessionmaker,
        settings_id: share.SettingsID,
        *,
        reg: share.Registry = share.DEFAULT_REGISTRY,
    ) -> Self:
        """
        Создать менеджер транзакций SqlAlchemy

        :param sessionmaker_: фабрика сессий SqlAlchemy
        :param settings_id: идентификатор настроек
        :param reg: реестр
        :return: менеджер транзакций
        :raises RegistryIsNotInitializedException: если реестр не инициализирован
        :raises SettingsNotFoundException: если настройки не найдены
        """
        ctx_manager = reg.get_ctx_manager()
        settings = reg.get_settings_by_id(settings_id)

        return cls(
            sessionmaker_=sessionmaker_,
            ctx_manager=ctx_manager,
            settings=settings,
        )

    async def _create_transaction(self) -> share.Transaction:
        return SqlAlchemyTransaction.create(self._sessionmaker)

    async def _create_nested_transaction(self) -> share.Transaction:
        return SqlAlchemyNestedTransaction.create(self._sessionmaker)
