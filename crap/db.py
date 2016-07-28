from motor.motor_asyncio import AsyncIOMotorClient


class Storage:

    def __init__(self, mongo_uri):
        self.db = AsyncIOMotorClient(mongo_uri)

    def find(self, collection):
        pass

    def update(self, collection):
        pass

    def insert(self, collection, document):
        pass

    def remove(self, collection):
        pass
