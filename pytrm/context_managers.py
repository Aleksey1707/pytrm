from typing import Optional

from pytrm import exceptions, interfaces, registries


class DefaultContextManager:
    """Базовая реализация контекстного менеджера"""

    __slots__ = ()

    @staticmethod
    def _get_default_key() -> interfaces.Key:
        settings = registries.DEFAULT_REGISTRY.get_default_settings()
        key = settings.key
        return key

    def get_default(self, ctx: interfaces.Context) -> interfaces.Transaction:
        key = self._get_default_key()
        return self.get_by_key(ctx, key)

    def set_default(self, ctx: interfaces.Context, transaction: interfaces.Transaction) -> interfaces.Context:
        key = self._get_default_key()
        return self.set_by_key(ctx, key, transaction)

    def get_by_key(self, ctx: interfaces.Context, key: interfaces.Key) -> interfaces.Transaction:
        transaction = ctx.get(key)
        if not isinstance(transaction, interfaces.Transaction):
            raise exceptions.UnknownValueInContextException

        return transaction

    def set_by_key(
        self,
        ctx: interfaces.Context,
        key: interfaces.Key,
        transaction: Optional[interfaces.Transaction],
    ) -> interfaces.Context:
        return ctx.set(key, transaction)
