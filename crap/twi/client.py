import http
from base64 import b64encode
from urllib.parse import urljoin

import aiohttp
import trafaret as t


class Client:

    token = None
    auth_headers = None
    result_types = ['recent', 'popular', 'mixed']
    default_count = 100

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
        url = urljoin(self.base_url, '/oauth2/token')
        resp = await self.session.post(url, data=payload, headers=headers)
        assert resp.status == http.HTTPStatus.OK, resp.status
        content = self.auth_resp.check(await resp.json())
        self._set_auth_headers(content['access_token'])

    def _set_auth_headers(self, token):
        self.auth_headers = {'Authorization': "Bearer %s" % token}

    async def search(self, q, result_type='recent'):
        url = urljoin(self.base_url, "/1.1/search/tweets.json")
        assert result_type in self.result_types
        params = {'q': q, 'lang': 'en', 'result_type': result_type, 'count': self.default_count,
                  'include_entities': 'true'}
        resp = await self.session.get(url, params=params, headers=self.auth_headers)
        assert resp.status == http.HTTPStatus.OK, str(http.HTTPStatus.OK) + await resp.text()
        content = await resp.json()
        return content

    def __del__(self):
        self.session.close()




