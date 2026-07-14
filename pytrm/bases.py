import abc
import contextlib
from typing import AsyncContextManager, AsyncIterator, Optional, Tuple, Type

from pytrm import exceptions, share


class BaseTransactionManager(abc.ABC):
    """Базовая реализация менеджера транзакций"""

    __slots__ = ("_ctx_manager", "_settings")

    _ctx_manager: share.ContextManager
    _settings: share.Settings

    def __init__(
        self,
        ctx_manager: share.ContextManager,
        settings: share.Settings,
    ) -> None:
        self._ctx_manager = ctx_manager
        self._settings = settings

    def do(
        self,
        ctx: share.ContextT,
        *,
        settings: Optional[share.Settings] = None,
        exclude: Tuple[Type[BaseException], ...] = (),
        propagation: Optional[share.Propagation] = None,
    ) -> AsyncContextManager[share.ContextT]:
        """
        Выполнить в транзакции

        :param ctx: контекст
        :param settings: настройки (если не указаны, используются настройки по умолчанию)
        :param exclude: типы исключений, при которых требуется фиксация изменений вместо отката
        :param propagation: правило распространения транзакции (переопределяет значение из настроек)
        :return: асинхронный контекстный менеджер с новым контекстом
        :raises BaseTrmException: если произошла ошибка при работе с транзакцией
        """
        return contextlib.asynccontextmanager(self._do)(ctx, settings, exclude, propagation)

    async def _do(
        self,
        ctx: share.ContextT,
        settings: Optional[share.Settings],
        exclude: Tuple[Type[BaseException], ...],
        propagation: Optional[share.Propagation],
    ) -> AsyncIterator[share.ContextT]:
        if settings is None:
            settings = self._settings

        if propagation is not None:
            settings = settings.with_propagation(propagation)

        ctx = await self._initialize(ctx, settings)

        key = settings.key
        try:
            transaction = self._ctx_manager.get(ctx, key)
        except exceptions.TransactionNotFoundInContextException as e:
            if settings.propagation not in (share.Propagation.NOT_SUPPORTED, share.Propagation.SUPPORTS):
                raise e

            yield ctx
        else:
            if transaction.is_active():
                yield ctx
            else:
                await transaction.begin()
                try:
                    yield ctx
                except Exception as e:
                    if isinstance(e, exclude):
                        await transaction.commit()
                    else:
                        await transaction.rollback()

                    raise e
                else:
                    await transaction.commit()

    async def _initialize(self, ctx: share.ContextT, settings: share.Settings) -> share.ContextT:
        key = settings.key

        try:
            self._ctx_manager.get(ctx, key)
        except exceptions.TransactionNotFoundInContextException:
            has_transaction = False
        else:
            has_transaction = True

        propagation = settings.propagation
        if propagation is share.Propagation.REQUIRED:
            if has_transaction:
                return ctx
        elif propagation is share.Propagation.NESTED:
            if has_transaction:
                transaction = await self._create_nested_transaction()
                ctx = self._ctx_manager.set(ctx, key, transaction)
                return ctx
        elif propagation is share.Propagation.MANDATORY:
            if has_transaction:
                return ctx

            raise exceptions.PropagationMandatoryTrmException
        elif propagation is share.Propagation.NEVER:
            if has_transaction:
                raise exceptions.PropagationNeverTrmException

            return ctx
        elif propagation is share.Propagation.NOT_SUPPORTED:
            if has_transaction:
                return self._ctx_manager.remove(ctx, key)

            return ctx
        elif propagation is share.Propagation.REQUIRES_NEW:
            pass
        elif propagation is share.Propagation.SUPPORTS:
            return ctx

        transaction = await self._create_transaction()
        return self._ctx_manager.set(ctx, key, transaction)

    async def _set_new_transaction(
        self,
        ctx: share.Context,
        key: share.Key,
    ) -> None:
        transaction = await self._create_transaction()
        self._ctx_manager.set(ctx, key, transaction)

    @abc.abstractmethod
    async def _create_transaction(self) -> share.Transaction: ...

    @abc.abstractmethod
    async def _create_nested_transaction(self) -> share.Transaction: ...
