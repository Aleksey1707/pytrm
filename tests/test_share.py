import pytest

import pytrm
from pytrm import exceptions, share
from tests import contexts
from tests.stubs import DummyTransaction


def test_context_manager_find_returns_none_when_missing() -> None:
    ctx_manager = share.ContextManager()
    ctx = contexts.Context.empty()

    assert ctx_manager.find(ctx, pytrm.Key("test")) is None


def test_context_manager_get_raises_when_missing() -> None:
    ctx_manager = share.ContextManager()
    ctx = contexts.Context.empty()

    with pytest.raises(exceptions.TransactionNotFoundInContextException):
        ctx_manager.get(ctx, pytrm.Key("test"))


def test_context_manager_get_raises_on_unknown_value() -> None:
    ctx_manager = share.ContextManager()
    ctx = contexts.Context.empty().set(pytrm.Key("test"), object())

    with pytest.raises(exceptions.UnknownValueInContextException):
        ctx_manager.get(ctx, pytrm.Key("test"))


def test_context_manager_set_and_remove() -> None:
    ctx_manager = share.ContextManager()
    ctx = contexts.Context.empty()
    key = pytrm.Key("test")
    transaction = DummyTransaction()

    new_ctx = ctx_manager.set(ctx, key, transaction)
    assert ctx_manager.get(new_ctx, key) is transaction

    cleared_ctx = ctx_manager.remove(new_ctx, key)
    assert ctx_manager.find(cleared_ctx, key) is None


def test_settings_storage_create_raises_on_empty() -> None:
    with pytest.raises(exceptions.NoSettingsException):
        share.SettingsStorage.create([])


def test_settings_storage_get_raises_when_not_found() -> None:
    settings = pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )
    storage = share.SettingsStorage.create([settings])

    with pytest.raises(exceptions.SettingsNotFoundException):
        storage.get("missing")


def test_settings_storage_get_returns_settings() -> None:
    settings = pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )
    storage = share.SettingsStorage.create([settings])

    assert storage.get("test") == settings


def test_registry_raises_when_not_initialized() -> None:
    registry = share.Registry()

    with pytest.raises(exceptions.RegistryIsNotInitializedException):
        registry.get_settings_by_id("test")


def test_registry_raises_on_double_initialize() -> None:
    settings = pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )
    storage = share.SettingsStorage.create([settings])
    registry = share.Registry()
    registry.initialize(storage, share.DEFAULT_CONTEXT_MANAGER, "_trm", "_trm_settings")

    with pytest.raises(exceptions.RegistryIsAlreadyInitializedException):
        registry.initialize(storage, share.DEFAULT_CONTEXT_MANAGER, "_trm", "_trm_settings")


def test_registry_get_trm_attr_name_raises_when_not_set() -> None:
    settings = pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )
    storage = share.SettingsStorage.create([settings])
    registry = share.Registry()
    registry.initialize(storage, share.DEFAULT_CONTEXT_MANAGER, None, "_trm_settings")

    with pytest.raises(exceptions.TrmAttrNameNoAtRegistryException):
        registry.get_trm_attr_name()


def test_registry_get_trm_settings_attr_name_raises_when_not_set() -> None:
    settings = pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )
    storage = share.SettingsStorage.create([settings])
    registry = share.Registry()
    registry.initialize(storage, share.DEFAULT_CONTEXT_MANAGER, "_trm", None)

    with pytest.raises(exceptions.TrmSettingsAttrNameNoAtRegistryException):
        registry.get_trm_settings_attr_name()


def test_registry_get_settings_and_ctx_manager() -> None:
    settings = pytrm.UniqSettings(
        id="test",
        key=pytrm.Key("test"),
        propagation=pytrm.Propagation.REQUIRED,
    )
    storage = share.SettingsStorage.create([settings])
    registry = share.Registry()
    registry.initialize(storage, share.DEFAULT_CONTEXT_MANAGER, "_trm", "_trm_settings")

    assert registry.get_settings_by_id("test") == settings
    assert registry.get_ctx_manager() is share.DEFAULT_CONTEXT_MANAGER
    assert registry.get_trm_attr_name() == "_trm"
    assert registry.get_trm_settings_attr_name() == "_trm_settings"
