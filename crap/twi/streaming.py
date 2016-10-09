import asyncio
import base64
import hmac
import json
import logging
import time
from hashlib import sha1
from pprint import pprint
from random import random
from urllib.parse import quote, urlsplit, urlunsplit, urljoin, urlencode

import oauthlib.oauth1 as oauth
import trafaret as t
from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class HmacSha1Signature:
    """HMAC-SHA1 signature-method."""
    name = 'HMAC-SHA1'

    @staticmethod
    def _escape(s):
        """URL escape a string."""
        bs = s.encode('utf-8')
        return quote(bs, '~').encode('utf-8')

    @staticmethod
    def _remove_qs(url):
        """Remove query string from an URL."""
        scheme, netloc, path, _, fragment = urlsplit(url)

        return urlunsplit((scheme, netloc, path, '', fragment))

    def sign(self, consumer_secret, method, url, oauth_token_secret=None, **params):
        """Create a signature using HMAC-SHA1."""
        params = "&".join("%s=%s" % (k, quote(str(value), '~'))
                          for k, value in sorted(params.items()))
        logger.debug("params: %s" % params)
        method = method.upper()
        url = self._remove_qs(url)

        signature = b"&".join(map(self._escape, (method, url, params)))

        key = self._escape(consumer_secret) + b"&"
        if oauth_token_secret:
            key += self._escape(oauth_token_secret)

        hashed = hmac.new(key, signature, sha1)
        return base64.b64encode(hashed.digest()).decode()


class StreamingClient:
    filter_endpoint = "/1.1/statuses/filter.json"
    sample_endpoint = "/1.1/statuses/sample.json"
    predicates = ["follow", "locations", "track"]
    keys = ['language', 'delimited', 'stall_warnings']
    trafaret = t.Dict({
        'api_key': t.String,
        'api_secret': t.String,
        'access_token': t.String,
        'access_secret': t.String,
        'stream': t.URL,
    }).ignore_extra('*')

    def __init__(self, config):
        config = self.trafaret.check(config)
        self.base_url = config['stream']
        self.signature = HmacSha1Signature()
        self.session = ClientSession()
        self.oauth_client = oauth.Client(
            client_key=config['api_key'],
            client_secret=config['api_secret'],
            resource_owner_key=config['access_token'],
            resource_owner_secret=config['access_secret']
        )

    async def request(self, method, endpoint, params=None, headers=None):
        url = urljoin(self.base_url, endpoint)
        headers = (headers or {})
        if method == 'POST':
            headers['Content-type'] = 'application/x-www-form-urlencoded'
        uri, signed_headers, body = self.oauth_client.sign(url, method, params, headers)
        logger.debug("PREPARED: %s %s %s", uri, signed_headers, body)
        resp = await self.session.request(method, uri, params=body, headers=signed_headers)
        return resp

    async def stream(self, queue, predicate, value, **kwargs):
        params = dict(((predicate, value,),))
        while True:
            resp = await self.request('POST', self.filter_endpoint, params)
            while True:
                data = await resp.content.readline()
                message = data.strip()
                if message != b'':
                    message = json.loads(message.decode('utf-8'))
                    logger.debug("Got something %s", message['id'])
                    await queue.put(message)
            await asyncio.sleep(10)

    def __del__(self):
        asyncio.ensure_future(self.session.close())
