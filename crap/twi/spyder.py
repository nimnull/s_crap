from urllib.parse import parse_qs

import injections

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

    async def get_twitts(self, params=None):

        rv = await self.twitter.search('python', params=params)

        statuses, metadata, max_id = self._parse_response(rv)
        logger.debug("Max id: %s" % max_id)
        # while max_id != history_arg['max_id']:
        #     statuses, max_id, history_arg = self._parse_response(rv)
        #     print("History: %s" % rv['search_metadata'])
        # await self.store_twitts(statuses)
        logger.debug("Meta: %s" % metadata)

        refresh_args = flatten_params(
            parse_qs(metadata['refresh_url'].strip('?'))
        )
        history_args = flatten_params(
            parse_qs(metadata['next_results'].strip('?'))
        )

        await self.dig_twitts_history(history_args)


        # await self.refresh_twitts(refresh_args)
        # await self.dig_twitts_history(history_arg)

    def _parse_response(self, response):
        statuses = response['statuses']
        metadata = response['search_metadata']
        max_id = metadata['max_id']
        return statuses, metadata, max_id

    async def refresh_twitts(self, params):
        rv = await self.twitter.search(params=params)
        metadata = rv['search_metadata']

    async def dig_twitts_history(self, query):
        call_next = query is not None

        while call_next:
            rv = await self.twitter.search(params=query)
            statuses, metadata, max_id = self._parse_response(rv)
            logger.debug("History meta: %s" % rv)

            call_next = metadata.get('next_results')
            query = call_next and flatten_params(
                parse_qs(metadata['next_results'].strip('?'))
            ) or None

    async def store_twitts(self, statuses):
        self.storage.update('twitter_raw', statuses)
