# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import math
import hmac
import base64
import hashlib


if sys.version_info > (3,):  # pragma: nocover
    IS_PY3 = True
    xrange = range
    byte_to_int = lambda x: x
    int_to_byte = lambda x: bytes((x,))
else:  # pragma: nocover
    IS_PY3 = False
    byte_to_int = ord
    int_to_byte = chr


def strings_differ(string1, string2):
    """Check whether two bytestrings differ while avoiding timing attacks.

    This function returns True if the given strings differ and False
    if they are equal.  It's careful not to leak information about *where*
    they differ as a result of its running time, which can be very important
    to avoid certain timing-related crypto attacks:

        http://seb.dbzteam.org/crypto/python-oauth-timing-hmac.pdf

    """
    if len(string1) != len(string2):
        return True
    invalid_bits = 0
    for a, b in zip(string1, string2):
        invalid_bits += byte_to_int(a) ^ byte_to_int(b)
    return invalid_bits != 0


def HKDF_extract(salt, IKM, hashmod=hashlib.sha256):
    """HKDF-Extract; see RFC-5869 for the details."""
    if salt is None:
        salt = b"\x00" * hashmod().digest_size
    return hmac.new(salt, IKM, hashmod).digest()


def HKDF_expand(PRK, info, L, hashmod=hashlib.sha256):
    """HKDF-Expand; see RFC-5869 for the details."""
    digest_size = hashmod().digest_size
    N = int(math.ceil(L * 1.0 / digest_size))
    assert N <= 255
    T = b""
    output = []
    for i in xrange(1, N + 1):
        data = T + info + int_to_byte(i)
        T = hmac.new(PRK, data, hashmod).digest()
        output.append(T)
    return b"".join(output)[:L]


def HKDF(secret, salt, info, size, hashmod=hashlib.sha256):
    """HKDF-extract-and-expand as a single function."""
    PRK = HKDF_extract(salt, secret, hashmod)
    return HKDF_expand(PRK, info, size, hashmod)


def encode_token_bytes(data):
    """Encode token data from bytes into a native string.

    This function base64-encodes binary data representing a token into a
    urlsafe native string.
    """
    data = base64.urlsafe_b64encode(data)
    if IS_PY3:  # pragma: nocover
        data = data.decode("ascii")
    return data


def decode_token_bytes(data):
    """Decode token data from a native string into bytes.

    This function base64-decodes binary data representing a token from a
    urlsafe native string.
    """
    if IS_PY3:  # pragma: nocover
        data = data.encode("ascii")
    return base64.urlsafe_b64decode(data)
