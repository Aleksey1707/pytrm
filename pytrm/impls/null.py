import contextlib
import copy
from typing import AsyncContextManager, AsyncIterator, Optional, Tuple, Type

from pytrm import share


class NullTransactionManager:
    """Null менеджер транзакций (не делает ничего, возвращает копию переданного контекста)"""

    def do(
        self,
        ctx: share.ContextT,
        settings: Optional[share.Settings] = None,
        exclude: Tuple[Type[BaseException], ...] = (),
    ) -> AsyncContextManager[share.ContextT]:
        """
        Выполнить в транзакции (без изменений)

        :param ctx: контекст
        :param settings: настройки (игнорируются)
        :param exclude: типы исключений (игнорируются)
        :return: асинхронный контекстный менеджер с копией контекста
        """
        return contextlib.asynccontextmanager(self._do)(ctx, settings, exclude)

    async def _do(
        self,
        ctx: share.ContextT,
        settings: Optional[share.Settings],
        exclude: Tuple[Type[BaseException], ...],
    ) -> AsyncIterator[share.ContextT]:
        ctx = copy.copy(ctx)
        yield ctx
