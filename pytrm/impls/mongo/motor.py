from motor.core import AgnosticClient, AgnosticClientSession

from pytrm import share
from pytrm.impls.mongo import base
from pytrm.impls.mongo.base import MongoSessionData as MongoSessionData
from pytrm.impls.mongo.base import MongoTransactionData as MongoTransactionData

MongoClient = AgnosticClient
MongoSession = AgnosticClientSession


class MongoTransaction(base.BaseMongoTransaction):
    """Обёртка над транзакцией MongoDB (motor)"""

    __slots__ = ()

    async def _start_transaction(self, transaction_data: base.MongoTransactionData) -> None:
        self._session.start_transaction(**transaction_data)  # type: ignore[attr-defined]


class MongoTransactionManager(base.BaseMongoTransactionManager[AgnosticClient]):
    """Менеджер транзакций MongoDB (motor)"""

    __slots__ = ()

    async def _create_transaction(self) -> share.Transaction:
        session = await self._client.start_session(**self._session_kwargs())
        # motor объявляет in_transaction методом, хотя в рантайме это свойство
        return MongoTransaction(session, self._transaction_data)  # type: ignore[arg-type]
