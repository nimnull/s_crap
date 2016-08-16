from motor.motor_asyncio import AsyncIOMotorClient

from crap.logs import logger


class Storage:

    def __init__(self, mongo_uri):
        self.mongo_client = AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client.get_default_database()

    def find(self, collection):
        pass

    async def update(self, collection, query, update, options):
        return await self.db[collection].update(query, update, **options)

    def insert(self, collection, document):
        pass

    def remove(self, collection):
        pass
