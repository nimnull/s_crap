from urllib.parse import parse_qs

import asyncio
import injections
import pymongo

from crap.db import Storage
from crap.logs import logger
from crap.twi.streaming import StreamingClient

from .client import Client


def flatten_params(params):
    query = dict()
    for k, v in params.items():
        query[k] = len(v) and v[0] or v
    return query


class BaseSpyder:
    storage = injections.depends(Storage)
    client = None
    twitter_raw = 'twitter_raw'

    def __injected__(self):
        self.storage.db[self.twitter_raw].create_index(
            [('id', pymongo.ASCENDING)], background=True, unique=True
        )

        if self.client is None:
            raise NotImplementedError('Should have twitter client class specified')

    async def store_twitts(self, statuses):
        logger.debug("Stored: %s", len(statuses))
        for st in statuses:
            await self.storage.update(self.twitter_raw,
                                      {'id': st['id']}, st, {'upsert': True})


@injections.has
class Spyder(BaseSpyder):
    client = injections.depends(Client)
    config = injections.depends(dict)

    async def get_twitts(self, params=None):

        while True:
            rv = await self.client.search('python', params=params)

            statuses, metadata = self._parse_response(rv)
            await self.store_twitts(statuses)

            logger.debug("Max id: %s" % metadata['max_id'])
            logger.debug("Meta: %s" % metadata)

            await self.dig_twitts_history(metadata)

            params = self.__get_params(metadata, 'refresh_url')
            await asyncio.sleep(self.config['twitter']['delay'])

    def _parse_response(self, response):
        statuses = response['statuses']
        metadata = response['search_metadata']
        return statuses, metadata

    def __get_params(self, metadata, key):
        next_results = metadata.get(key)

        query = next_results and flatten_params(
            parse_qs(next_results.strip('?'))
        ) or None

        return query

    async def dig_twitts_history(self, metadata):

        while 'next_results' in metadata:
            logger.debug("History meta: %s" % metadata)
            params = self.__get_params(metadata, 'next_results')
            rv = await self.twitter.search(params=params)
            statuses, metadata = self._parse_response(rv)
            await self.store_twitts(statuses)


@injections.has
class StreamingSpyder(BaseSpyder):
    client = injections.depends(StreamingClient)
    config = injections.depends(dict)

    def __init__(self):
        self.queue = asyncio.Queue(maxsize=10)

    async def get_twitts(self):
        asyncio.ensure_future(self.client.stream(self.queue, predicate='track', value='python'))

        while True:
            item = await self.queue.get()
            print(item)
