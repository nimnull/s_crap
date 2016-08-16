from urllib.parse import parse_qs

import asyncio
import injections
import pymongo

from crap.db import Storage
from crap.logs import logger
from .client import Client


def flatten_params(params):
    query = dict()
    for k, v in params.items():
        query[k] = len(v) and v[0] or v
    return query


@injections.has
class Spyder:
    storage = injections.depends(Storage)
    twitter = injections.depends(Client)
    config = injections.depends(dict)
    twitter_raw = 'twitter_raw'

    def __init__(self):
        self.storage.db[self.twitter_raw].create_index(
            [('id', pymongo.ASCENDING)], background=True, unique=True
        )

    async def get_twitts(self, params=None):

        while True:
            rv = await self.twitter.search('python', params=params)

            statuses, metadata = self._parse_response(rv)
            await self.store_twitts(statuses)

            logger.debug("Max id: %s" % metadata['max_id'])
            logger.debug("Meta: %s" % metadata)

            next_results = self.__get_next_query(metadata)

            if next_results:
                await self.dig_twitts_history(next_results)

            params = flatten_params(
                parse_qs(metadata['refresh_url'].strip('?'))
            )
            await asyncio.sleep(self.config['twitter']['delay'])

    def _parse_response(self, response):
        statuses = response['statuses']
        metadata = response['search_metadata']
        return statuses, metadata

    def __get_next_query(self, metadata):
        next_results = metadata.get('next_results')

        query = next_results and flatten_params(
            parse_qs(next_results.strip('?'))
        ) or None

        return query

    async def dig_twitts_history(self, query):
        call_next = query is not None

        while call_next:
            rv = await self.twitter.search(params=query)
            statuses, metadata = self._parse_response(rv)
            await self.store_twitts(statuses)
            logger.debug("History meta: %s" % metadata)
            call_next = metadata.get('next_results')
            query = self.__get_next_query(metadata)

    async def store_twitts(self, statuses):
        logger.debug("Stored: %s", len(statuses))
        for st in statuses:
            await self.storage.update(self.twitter_raw,
                                      {'id': st['id']}, st, {'upsert': True})
