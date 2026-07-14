from typing import Hashable

from motor.motor_asyncio import AsyncIOMotorCollection

import pytrm
from tests.mongo.base_repos import BaseMongoRepository


class MotorMongoRepository(BaseMongoRepository):
    def __init__(self, collection: AsyncIOMotorCollection, settings_id: Hashable, reg: pytrm.Registry) -> None:
        super().__init__(collection=collection, settings_id=settings_id, reg=reg)
