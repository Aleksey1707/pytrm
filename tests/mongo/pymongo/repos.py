from typing import Hashable

from pymongo.asynchronous.collection import AsyncCollection

import pytrm
from tests.mongo.base_repos import BaseMongoRepository


class PymongoMongoRepository(BaseMongoRepository):
    def __init__(self, collection: AsyncCollection, settings_id: Hashable, reg: pytrm.Registry) -> None:
        super().__init__(collection=collection, settings_id=settings_id, reg=reg)
