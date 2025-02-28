import contextlib
import copy
from typing import AsyncContextManager, AsyncIterator, Optional, Tuple, Type

from pytrm import share


class NullTransactionManager:
    """Null менеджер транзакций (не делает ничего, возвращает копию переданного контекста)"""

    def do(
        self,
        ctx: share.Context,
        settings: Optional[share.Settings] = None,
        exclude: Tuple[Type[BaseException], ...] = (),
    ) -> AsyncContextManager[share.Context]:
        return contextlib.asynccontextmanager(self._do)(ctx, settings, exclude)

    async def _do(
        self,
        ctx: share.Context,
        settings: Optional[share.Settings],
        exclude: Tuple[Type[BaseException], ...],
    ) -> AsyncIterator[share.Context]:
        ctx = copy.copy(ctx)
        yield ctx
