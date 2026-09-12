from pymongo import AsyncMongoClient
from pymongo.asynchronous.client_session import AsyncClientSession

from pytrm import share
from pytrm.impls.mongo import base
from pytrm.impls.mongo.base import MongoSessionData as MongoSessionData
from pytrm.impls.mongo.base import MongoTransactionData as MongoTransactionData

MongoClient = AsyncMongoClient
MongoSession = AsyncClientSession


class MongoTransaction(base.BaseMongoTransaction):
    """Обёртка над транзакцией MongoDB (pymongo)"""

    __slots__ = ()

    async def _start_transaction(self, transaction_data: base.MongoTransactionData) -> None:
        await self._session.start_transaction(**transaction_data)  # type: ignore[attr-defined]


class MongoTransactionManager(base.BaseMongoTransactionManager[AsyncMongoClient]):
    """Менеджер транзакций MongoDB (pymongo)"""

    __slots__ = ()

    async def _create_transaction(self) -> share.Transaction:
        session = self._client.start_session(**self._session_kwargs())
        return MongoTransaction(session, self._transaction_data)
