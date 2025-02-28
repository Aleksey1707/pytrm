import contextlib
import copy
from typing import AsyncContextManager, AsyncIterator, Optional

from pytrm import share


class NullTransactionManager:
    """Null менеджер транзакций (не делает ничего, возвращает копию переданного контекста)"""

    def do(
        self,
        ctx: share.Context,
        settings: Optional[share.Settings] = None,
    ) -> AsyncContextManager[share.Context]:
        return contextlib.asynccontextmanager(self._do)(ctx, settings)

    async def _do(
        self,
        ctx: share.Context,
        settings: Optional[share.Settings],
    ) -> AsyncIterator[share.Context]:
        ctx = copy.copy(ctx)
        yield ctx
