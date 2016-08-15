import aiohttp
import asyncio
import http
import time
import trafaret as t

from base64 import b64encode
from functools import wraps
from urllib.parse import urljoin

from crap.logs import logger


class RateLimitExceedError(Exception):
    message = "Rate limit exceed"


def limit_rate_by(limit_attr_name, reset_time_attr):

    def closure(fn):

        @wraps(fn)
        def wrapper(instance, *args, **kwargs):
            rl = getattr(instance, limit_attr_name)
            logger.debug("Rate limit: %s" % rl)
            reset_time = getattr(instance, reset_time_attr)
            timeleft = reset_time - time.time()
            logger.debug("Time left: %s" % timeleft)

            if rl <= 0 and timeleft > 0:
                asyncio.sleep(timeleft)
            else:
                return fn(instance, *args, **kwargs)

        return wrapper

    return closure


class Client:

    token = None
    auth_headers = None
    result_types = ['recent', 'popular', 'mixed']
    search_uri = "/1.1/search/tweets.json"
    oauth_uri = "/oauth2/token"
    default_count = 10
    _rate_limit = 1
    _rate_limit_reset = 0

    trafaret = t.Dict({
        'api_key': t.String,
        'api_secret': t.String,
        'url': t.URL
    }).ignore_extra('*')

    auth_resp = t.Dict({
        'token_type': t.String,
        'access_token': t.String
    }).ignore_extra('*')

    def __init__(self, config):
        config = self.trafaret.check(config)
        self.base_url = config['url']
        self.bearer = ":".join([config['api_key'], config['api_secret']]).encode()
        self.session = aiohttp.ClientSession()

    async def auth(self):
        headers = {'Authorization': "Basic %s" % b64encode(self.bearer).decode()}
        payload = {'grant_type': 'client_credentials'}
        url = urljoin(self.base_url, self.oauth_uri)
        resp = await self.session.post(url, data=payload, headers=headers)
        assert resp.status == http.HTTPStatus.OK, resp.status
        content = self.auth_resp.check(await resp.json())
        self._set_auth_headers(content['access_token'])

    def _set_auth_headers(self, token):
        self.auth_headers = {'Authorization': "Bearer %s" % token}

    @limit_rate_by('_rate_limit', '_rate_limit_reset')
    async def search(self, q=None, result_type='recent', params=None):
        assert result_type in self.result_types
        await self.ensure_authenticated()

        url = urljoin(self.base_url, self.search_uri)
        default_params = {'q': q, 'lang': 'en', 'result_type': result_type, 'count': self.default_count,
                  'include_entities': 'true'}

        if params is not None:
            default_params.update(params)

        print("Max id: %s" % default_params.get('max_id'))

        resp = await self.session.get(url, params=default_params, headers=self.auth_headers)
        assert resp.status == http.HTTPStatus.OK, str(http.HTTPStatus.OK) + await resp.text()

        self._rate_limit_reset = int(resp.headers['X-RATE-LIMIT-RESET'])
        self._rate_limit = int(resp.headers['X-RATE-LIMIT-REMAINING'])
        logger.debug("Remaining calls: %s" % self._rate_limit)

        content = await resp.json()
        return content

    async def ensure_authenticated(self):
        if self.auth_headers is None:
            await self.auth()


    def __del__(self):
        self.session.close()




