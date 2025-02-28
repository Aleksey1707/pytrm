from typing import Any, Hashable, Mapping

import bson
from motor.motor_asyncio import AsyncIOMotorCollection

import pytrm
from tests import contexts
from tests.repositories import EntityNotFoundRepositoryException, Repository


class MotorMongoRepository(Repository[Mapping[str, Any], bson.ObjectId]):

    def __init__(self, collection: AsyncIOMotorCollection, settings_id: Hashable, reg: pytrm.Registry) -> None:
        self._collection = collection
        self._settings_id = settings_id
        self._reg = reg

    async def get(self, id_: bson.ObjectId, *, context: contexts.Context) -> Mapping[str, Any]:
        document = await self._collection.find_one({"_id": id_})
        if document is None:
            raise EntityNotFoundRepositoryException

        return document

    async def save(self, entity: Mapping[str, Any], *, context: contexts.Context) -> None:
        session = self._get_session(context)
        await self._collection.insert_one(entity, session=session)

    async def delete(self, id_: bson.ObjectId, *, context: contexts.Context) -> None:
        session = self._get_session(context)
        await self._collection.delete_one({"_id": id_}, session=session)

    def _get_session(self, context: contexts.Context) -> pytrm.Tr:
        return pytrm.get_native_transaction(context, self._settings_id, reg=self._reg)
