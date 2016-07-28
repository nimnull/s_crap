import injections

from crap.db import Storage
from .client import Client


@injections.has
class Spyder:
    storage = injections.depends(Storage)
    twitter = injections.depends(Client)

    async def store_twitts(self):

        if self.twitter.auth_headers is None:
            await self.twitter.auth()
        rv = await self.twitter.search('python')
        self.storage.insert('twitter_raw', rv)
