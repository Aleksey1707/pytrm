from typing import List, Optional

import pytest

import pytrm
from pytrm import exceptions
from pytrm.impls.mongo import base

pytestmark = pytest.mark.asyncio


async def test_commit_ends_session() -> None:
    session = StubSession()
    transaction = StubMongoTransaction(session)

    await transaction.commit()

    assert session.commited is True
    assert session.ended is True


async def test_rollback_ends_session() -> None:
    session = StubSession()
    transaction = StubMongoTransaction(session)

    await transaction.rollback()

    assert session.aborted is True
    assert session.ended is True


async def test_session_is_ended_when_commit_fails() -> None:
    # given: сессия, у которой падает фиксация
    session = StubSession(fail_on="commit")
    transaction = StubMongoTransaction(session)

    # when: фиксация
    with pytest.raises(RuntimeError):
        await transaction.commit()

    # then: сессия всё равно закрыта, а не подтекает
    assert session.ended is True


async def test_session_is_ended_when_rollback_fails() -> None:
    session = StubSession(fail_on="rollback")
    transaction = StubMongoTransaction(session)

    with pytest.raises(RuntimeError):
        await transaction.rollback()

    assert session.ended is True


async def test_begin_passes_transaction_data() -> None:
    session = StubSession()
    transaction = StubMongoTransaction(session, {"read_concern": "majority"})

    await transaction.begin()

    assert transaction.started_with == [{"read_concern": "majority"}]


async def test_begin_passes_empty_data_by_default() -> None:
    session = StubSession()
    transaction = StubMongoTransaction(session)

    await transaction.begin()

    assert transaction.started_with == [{}]


async def test_is_active_reflects_session() -> None:
    session = StubSession()
    transaction = StubMongoTransaction(session)
    assert transaction.is_active() is False

    session.in_transaction = True

    assert transaction.is_active() is True


async def test_unwrap_returns_session() -> None:
    session = StubSession()
    transaction = StubMongoTransaction(session)

    assert transaction.unwrap() is session


async def test_nested_transactions_are_not_supported(
    stub_manager: "StubMongoTransactionManager",
) -> None:
    transaction = StubMongoTransaction(StubSession())

    with pytest.raises(exceptions.NestedTransactionsNotSupportedTrmException):
        await stub_manager._create_nested_transaction(transaction)


async def test_session_kwargs_default_to_empty(
    stub_manager: "StubMongoTransactionManager",
) -> None:
    assert stub_manager._session_kwargs() == {}


class StubSession:
    def __init__(self, fail_on: str = "") -> None:
        self.in_transaction = False
        self.commited = False
        self.aborted = False
        self.ended = False
        self._fail_on = fail_on

    async def commit_transaction(self) -> None:
        if self._fail_on == "commit":
            raise RuntimeError("commit failed")

        self.commited = True

    async def abort_transaction(self) -> None:
        if self._fail_on == "rollback":
            raise RuntimeError("abort failed")

        self.aborted = True

    async def end_session(self) -> None:
        self.ended = True


class StubMongoTransaction(base.BaseMongoTransaction):
    def __init__(
        self,
        session: StubSession,
        transaction_data: Optional[base.MongoTransactionData] = None,
    ) -> None:
        super().__init__(session, transaction_data)
        self.started_with: List[base.MongoTransactionData] = []

    async def _start_transaction(self, transaction_data: base.MongoTransactionData) -> None:
        self.started_with.append(transaction_data)


class StubMongoTransactionManager(base.BaseMongoTransactionManager[object]):
    async def _create_transaction(self) -> StubMongoTransaction:
        return StubMongoTransaction(StubSession(), self._transaction_data)


@pytest.fixture
def stub_manager(
    settings: pytrm.UniqSettings,
    registry: pytrm.Registry,
) -> StubMongoTransactionManager:
    return StubMongoTransactionManager.create(object(), settings.id, reg=registry)
