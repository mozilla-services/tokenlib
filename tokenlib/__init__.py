# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
# pylint: disable=C0103
"""
Generic library for managing signed authentication tokens.
"""

__version__      = "2.0.0"
__description__  = "Generic library for managing signed authentication tokens."
__url__          = "https://github.com/mozilla-services/tokenlib"
__license__      = "MPLv2.0"
__author__       = 'Mozilla Services'
__author_email__ = 'services-dev@mozilla.org'
__keywords__     = 'authentication token'


import os
import logging
import time
import json
import hmac
import hashlib
import warnings
from binascii import hexlify

from tokenlib import errors
from tokenlib.utils import (strings_differ, HKDF,
                            encode_token_bytes, decode_token_bytes)


logger = logging.getLogger('tokenlib')


#  Default parameters for the TokenManager class.
#  We store these at module level so that module-level convenience
#  functions will have a consistent view of e.g. the default secret.
DEFAULT_SECRET = os.urandom(32)
DEFAULT_TIMEOUT = 5 * 60
DEFAULT_HASHMOD = "sha256"


#  Unique info strings for mixing into HKDF.
HKDF_INFO_SIGNING = b"services.mozilla.com/tokenlib/v1/signing"
HKDF_INFO_DERIVE = b"services.mozilla.com/tokenlib/v1/derive/"


class TokenManager(object):
    """Class for managing signed authentication tokens.

    This class provides a generic facility for creating and verifying signed
    authentication tokens.  It's useful as a basis for token-based auth schemes
    such as Two-Legged OAuth or MAC Access Auth, and should provide a good
    balance between speed, memory usage and security for most applications.

    The TokenManager must be initialized with a "master secret" which is used
    to crytographically secure the tokens.  Each token consists of a JSON
    object with an appended HMAC signature.  Tokens also have a corresponding
    "derived secret" generated using HKDF, which can be given to clients for
    use in signature-based authentication schemes.

    The constructor takes the following arguments:

       * secret:  string key used for signing the token;
                  if not specified then a random bytestring is used.

       * timeout: the time after which a token will expire, in seconds.

       * hashmod:  the hashing module to use for various HMAC operations;
                   if not specified then hashlib.sha256 will be used

    """

    def __init__(self, secret=None, timeout=None, hashmod=None):
        if secret is None:
            secret = DEFAULT_SECRET
        if not isinstance(secret, bytes):
            secret = secret.encode("utf8")
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        if hashmod is None:
            hashmod = DEFAULT_HASHMOD
        if isinstance(hashmod, str):
            hashmod = getattr(hashlib, hashmod)
        self.secret = secret
        self.timeout = timeout
        self.hashmod = hashmod
        hashobj = hashmod()
        self.hashmod_name = hashobj.name
        self.hashmod_digest_size = hashobj.digest_size
        self._sig_secret = HKDF(self.secret, salt=None,
                                info=HKDF_INFO_SIGNING,
                                size=self.hashmod_digest_size,
                                hashmod=self.hashmod)

    def make_token(self, data):
        """Generate a new token embedding the given dict of data.

        The token is a JSON dump of the given data along with an expiry
        time and salt.  It has a HMAC signature appended and is b64-encoded
        for transmission.
        """
        data = data.copy()
        if "salt" not in data:
            data["salt"] = hexlify(os.urandom(3)).decode("ascii")
        if "expires" not in data:
            data["expires"] = time.time() + self.timeout
        payload = json.dumps(data).encode("utf8")
        sig = self._get_signature(payload)
        assert len(sig) == self.hashmod_digest_size
        return encode_token_bytes(payload + sig)

    def parse_token(self, token, now=None):
        """Extract the data embedded in the given token, if valid.

        The token is valid if it has a valid signature and if the embedded
        expiry time has not passed.  If the token is not valid then this
        method raises ValueError.
        """
        # Parse the payload and signature from the token.
        try:
            decoded_token = decode_token_bytes(token)
        except (TypeError, ValueError) as e:
            raise errors.MalformedTokenError(str(e))
        payload = decoded_token[:-self.hashmod_digest_size]
        sig = decoded_token[-self.hashmod_digest_size:]
        # Carefully check the signature.
        # This is a deliberately slow string-compare to avoid timing attacks.
        # Read the docstring of strings_differ for more details.
        expected_sig = self._get_signature(payload)
        if strings_differ(sig, expected_sig):
            raise errors.InvalidSignatureError()
        # Only decode *after* we've confirmed the signature.
        # This should never fail, but well, you can't be too careful.
        try:
            data = json.loads(payload.decode("utf8"))
        except ValueError as e:  # pragma: nocover
            raise errors.MalformedTokenError(str(e))
        # Check whether it has expired.
        if now is None:
            now = time.time()
        if data["expires"] <= now:
            raise errors.ExpiredTokenError()
        return data

    def get_token_secret(self, token):
        """Get the derived secret key associated with the given token.

        A per-token secret key is calculated by deriving it from the master
        secret with HKDF.

        DEPRECATED: use the get_derived_secret() method instead.
        """
        warnings.warn("get_token_secret is deprecated; use get_derived_secret",
                      category=DeprecationWarning)
        return self.get_derived_secret(token)

    def get_derived_secret(self, token):
        """Get the derived secret key associated with the given token.

        A per-token secret key is calculated by deriving it from the master
        secret with HKDF.
        """
        try:
            payload = decode_token_bytes(token)[:-self.hashmod_digest_size]
            salt = json.loads(payload.decode("utf8"))["salt"].encode("ascii")
        except (TypeError, KeyError, ValueError) as e:
            raise errors.MalformedTokenError(str(e))
        info = HKDF_INFO_DERIVE + token.encode("ascii")
        secret = HKDF(self.secret, salt=salt, info=info,
                      size=self.hashmod_digest_size, hashmod=self.hashmod)
        return encode_token_bytes(secret)

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
    """Convenience function to get the derived secret key for a given token.

    DEPRECATED: use get_derived_secret() instead.
    """
    return TokenManager(**kwds).get_token_secret(token)


def get_derived_secret(token, **kwds):
    """Convenience function to get the derived secret key for a given token."""
    return TokenManager(**kwds).get_derived_secret(token)
