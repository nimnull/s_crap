import base64
import hmac
import logging
from hashlib import sha1
from random import random
from urllib.parse import quote, urlsplit, urlunsplit

import time

logger = logging.getLogger(__name__)


class Signature(object):
    """Abstract base class for signature methods."""
    name = None

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

    def sign(self, method, url, consumer_secret, oauth_token_secret=None, **params):
        """Abstract method."""
        raise NotImplementedError('Should not be called.')


class HmacSha1Signature(Signature):
    """HMAC-SHA1 signature-method."""
    name = 'HMAC-SHA1'

    def sign(self, consumer_secret, method, url, oauth_token_secret=None, **params):
        """Create a signature using HMAC-SHA1."""
        params = "&".join("%s=%s" % (k, quote(str(value), '~'))
                          for k, value in sorted(params.items()))
        method = method.upper()
        url = self._remove_qs(url)

        signature = b"&".join(map(self._escape, (method, url, params)))

        key = self._escape(consumer_secret) + b"&"
        if oauth_token_secret:
            key += self._escape(oauth_token_secret)

        hashed = hmac.new(key, signature, sha1)
        return base64.b64encode(hashed.digest()).decode()


def prepare_request(consumer_key, consumer_secret, oauth_token, oauth_token_secret, url, method, params):
    """Make a request to provider."""
    signature = HmacSha1Signature()
    oparams = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': sha1(str(random()).encode('ascii')).hexdigest(),
        'oauth_signature_method': signature.name,
        'oauth_timestamp': int(time.time()),
        'oauth_version': '1.0',
    }
    oparams.update(params or {})

    if oauth_token:
        oparams['oauth_token'] = oauth_token

    oparams['oauth_signature'] = signature.sign(
        method, url, consumer_secret, oauth_token_secret, **oparams
    )
    logger.debug("%s %s", url, oparams)
    return method, url, oparams
