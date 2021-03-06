import time
import hashlib
import hmac
from urllib.parse import urlparse


# From BitMEX API sample code:
# https://github.com/BitMEX/sample-market-maker/blob/master/market_maker/auth/APIKeyAuthWithExpires.py
class APIKeyAuthWithExpires(object):
    """Attaches API Key Authentication to the given Request object. This implementation uses `expires`."""
    def __init__(self, apiKey, apiSecret):
        """Init with Key & Secret."""
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    def __call__(self, r):
        """
        Called when forming a request - generates api key headers. This call uses `expires` instead of nonce.
        This way it will not collide with other processes using the same API Key if requests arrive out of order.
        For more details, see https://www.bitmex.com/app/apiKeys
        """
        # modify and return the request
        expires = int(round(time.time()) + 5)  # 5s grace period in case of clock skew
        r.headers['api-expires'] = str(expires)
        r.headers['api-key'] = self.apiKey
        r.headers['api-signature'] = self.generate_signature(self.apiSecret, r.method, r.url, expires, r.body or '')
        return r

    # From BitMEX API Documentation: https://www.bitmex.com/app/apiKeysUsage
    # Generates an API signature.
    # A signature is HMAC_SHA256(secret, verb + path + expires + data), hex encoded.
    # Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
    # and the data, if present, must be JSON without whitespace between keys.
    @staticmethod
    def generate_signature(secret, verb, url, expires, data):
        """Generate a request signature compatible with BitMEX."""
        # Parse the url so we can remove the base and extract just the path.
        parsedURL = urlparse(url)
        path = parsedURL.path
        if parsedURL.query:
            path = path + '?' + parsedURL.query

        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf8')

        message = verb + path + str(expires) + data

        signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
        return signature