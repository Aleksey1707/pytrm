import sys

from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from pytrm import bases, exceptions, share

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


class RedisTransaction:
    """Обёртка над пакетом команд Redis (MULTI/EXEC через pipeline).

    Команды внутри транзакции только накапливаются в pipeline и не возвращают
    результат до ``commit()`` (``await pipeline.execute()``). Чтение значений
    внутри блока ``do()`` невозможно — используйте отдельный клиент вне транзакции.
    Команды можно добавлять без ``await`` (``pipe.set(...)`` возвращает сам pipe).
    """

    __slots__ = ("_pipeline", "_is_active")

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline
        self._is_active = False

    def is_active(self) -> bool:
        """
        Проверить, активна ли транзакция

        :return: True, если транзакция активна
        """
        return self._is_active

    async def begin(self) -> None:
        """Начать транзакцию"""
        self._is_active = True

    async def commit(self) -> None:
        """Зафиксировать транзакцию"""
        try:
            await self._pipeline.execute()
        finally:
            self._is_active = False

    async def rollback(self) -> None:
        """Откатить транзакцию"""
        try:
            await self._pipeline.reset()
        finally:
            self._is_active = False

    def unwrap(self) -> share.NativeTransaction:
        """
        Получить нативный pipeline Redis

        :return: pipeline Redis
        """
        return self._pipeline


class RedisTransactionManager(bases.BaseTransactionManager):
    """Менеджер транзакций Redis (redis-py, async).

    Поддерживает только standalone/Sentinel клиент ``redis.asyncio.Redis``.
    Один pipeline не предназначен для параллельного использования из нескольких корутин.
    """

    __slots__ = ("_client",)

    def __init__(
        self,
        ctx_manager: share.ContextManager,
        settings: share.UniqSettings,
        client: Redis,
    ) -> None:
        super().__init__(ctx_manager, settings)
        self._client = client

    @classmethod
    def create(
        cls,
        client: Redis,
        settings_id: share.SettingsID,
        *,
        reg: share.Registry = share.DEFAULT_REGISTRY,
    ) -> Self:
        """
        Создать менеджер транзакций Redis

        :param client: клиент Redis
        :param settings_id: идентификатор настроек
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
        )

    async def _create_transaction(self) -> share.Transaction:
        return RedisTransaction(self._client.pipeline(transaction=True))

    async def _create_nested_transaction(self, transaction: share.Transaction) -> share.Transaction:
        raise exceptions.NestedTransactionsNotSupportedTrmException
