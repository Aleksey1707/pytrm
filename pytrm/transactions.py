from pytrm import interfaces, registries


def get_native_transaction(ctx: interfaces.Context, settings_id: interfaces.SettingsID) -> interfaces.Tr:
    """Найти нативную транзакцию"""
    return _get_native_transaction_by_reg(ctx, settings_id, registries.DEFAULT_REGISTRY)


def _get_native_transaction_by_reg(
    ctx: interfaces.Context,
    settings_id: interfaces.SettingsID,
    reg: registries.Registry,
) -> interfaces.Tr:
    settings = reg.get_settings_by_id(settings_id)
    ctx_manager = reg.get_ctx_manager()
    key = settings.key

    transaction = ctx_manager.get_by_key(ctx, key)
    return transaction.unwrap()
