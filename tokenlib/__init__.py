# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
"""

Generic library for managing signed authentication tokens.

"""

__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 0
__ver_sub__ = ""
__ver_tuple__ = (__ver_major__, __ver_minor__, __ver_patch__, __ver_sub__)
__version__ = "%d.%d.%d%s" % __ver_tuple__


import logging
import os
import time
import json
import hmac
import hashlib
from base64 import urlsafe_b64encode as b64encode
from base64 import urlsafe_b64decode as b64decode

from tokenlib.utils import strings_differ, HKDF


logger = logging.getLogger('tokenlib')


#  Default parameters for the TokenManager class.
#  We store these at module level so that module-level convenience
#  functions will have a consistent view of e.g. the default secret.
DEFAULT_SECRET = os.urandom(32)
DEFAULT_TIMEOUT = 5 * 60
DEFAULT_HASHMOD = hashlib.sha1


class TokenManager(object):
    """Class for managing signed authentication tokens.

    This class provides a generic facility for creating and verifying signed
    authentication tokens.  It's useful as a basis for token-based auth schemes
    such as Two-Legged OAuth or MAC Access Auth, and should provide a good
    balance between speed, memory usage and security for most applications.

    The TokenManager must be initialized with a "master secret" which is used
    to crytographically secure the tokens.  Each token consists of a JSON
    object with an appended HMAC signature.  Tokens also have a corresponding
    "token secret" generated using HKDF, which can be given to clients for
    use in signature-based authentication schemes.

    The constructor takes the following arguments:

       * secret:  string key used for signing the token;
                  if not specified then a random bytestring is used.

       * timeout: the time after which a token will expire.

       * hashmod:  the hashing module to use for various HMAC operations;
                   if not specified then hashlib.sha1 will be used.

    """

    def __init__(self, secret=None, timeout=None, hashmod=None):
        if secret is None:
            secret = DEFAULT_SECRET
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        if hashmod is None:
            hashmod = DEFAULT_HASHMOD
        if isinstance(hashmod, basestring):
            hashmod = getattr(hashlib, hashmod)
        self.secret = secret
        self.timeout = timeout
        self.hashmod = hashmod
        self.hashmod_digest_size = hashmod().digest_size
        self._sig_secret = HKDF(self.secret, salt=None, info="SIGNING",
                                size=self.hashmod_digest_size)

    def make_token(self, data):
        """Generate a new token embedding the given dict of data.

        The token is a JSON dump of the given data along with an expiry
        time and salt.  It has a HMAC signature appended and is b64-encoded
        for transmission.
        """
        data = data.copy()
        if "salt" not in data:
            data["salt"] = os.urandom(3).encode("hex")
        if "expires" not in data:
            data["expires"] = time.time() + self.timeout
        payload = json.dumps(data)
        sig = self._get_signature(payload)
        assert len(sig) == self.hashmod_digest_size
        return b64encode(payload + sig)

    def parse_token(self, token, now=None):
        """Extract the data embedded in the given token, if valid.

        The token is valid is it has a valid signature and if the embedded
        expiry time has not passed.  If the token is not valid then this
        method raises ValueError.
        """
        # Parse the payload and signature from the token.
        try:
            decoded_token = b64decode(token)
        except TypeError, e:
            raise ValueError(str(e))
        payload = decoded_token[:-self.hashmod_digest_size]
        sig = decoded_token[-self.hashmod_digest_size:]
        # Carefully check the signature.
        # This is a deliberately slow string-compare to avoid timing attacks.
        # Read the docstring of strings_differ for more details.
        expected_sig = self._get_signature(payload)
        if strings_differ(sig, expected_sig):
            raise ValueError("token has invalid signature")
        # Only decode *after* we've confirmed the signature.
        data = json.loads(payload)
        # Check whether it has expired.
        if now is None:
            now = time.time()
        if data["expires"] <= now:
            raise ValueError("token has expired")
        return data

    def get_token_secret(self, token):
        """Get the secret key associated with the given token.

        A per-token secret key is calculated by deriving it from the master
        secret with HKDF.
        """
        size = self.hashmod_digest_size
        # XXX: Having to parse the salt back out of the token is yuck.
        # But I like having get_token_secret() as an independent method.
        # We should consider modifying token format to make this easier.
        # e.g. by having token = b64encode(data):salt:signature.
        try:
            payload = b64decode(token)[:-self.hashmod_digest_size]
            salt = json.loads(payload)["salt"].encode("ascii")
        except (TypeError, KeyError), e:
            raise ValueError(str(e))
        secret = HKDF(self.secret, salt=salt, info=token, size=size)
        return b64encode(secret)

    def _get_signature(self, value):
        """Calculate the HMAC signature for the given value."""
        return hmac.new(self._sig_secret, value, self.hashmod).digest()


def make_token(data, **kwds):
    """Convenience function to make a token from the given data."""
    return TokenManager(**kwds).make_token(data)


def parse_token(token, now=None, **kwds):
    """Convenience function to parse data from the given token."""
    return TokenManager(**kwds).parse_token(token, now=now)


def get_token_secret(token, **kwds):
    """Convenience function to get the secret key for a given token."""
    return TokenManager(**kwds).get_token_secret(token)
