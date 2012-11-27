# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import hashlib
from binascii import unhexlify

if sys.version_info < (2, 7):
    import unittest2 as unittest  # pragma: nocover
else:
    import unittest  # pragma: nocover  # NOQA

from tokenlib.utils import strings_differ, HKDF, HKDF_extract


class TestUtils(unittest.TestCase):

    def test_strings_differ(self):
        # We can't really test the timing-invariance, but
        # we can test that we actually compute equality!
        self.assertTrue(strings_differ(b"", b"a"))
        self.assertTrue(strings_differ(b"b", b"a"))
        self.assertTrue(strings_differ(b"cc", b"a"))
        self.assertTrue(strings_differ(b"cc", b"aa"))
        self.assertFalse(strings_differ(b"", b""))
        self.assertFalse(strings_differ(b"D", b"D"))
        self.assertFalse(strings_differ(b"EEE", b"EEE"))

    def test_hkdf_rfc_case1(self):
        hashmod = hashlib.sha256
        IKM = unhexlify(b"0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b")
        salt = unhexlify(b"000102030405060708090a0b0c")
        info = unhexlify(b"f0f1f2f3f4f5f6f7f8f9")
        L = 42
        PRK = unhexlify(b"077709362c2e32df0ddc3f0dc47bba63") +\
              unhexlify(b"90b6c73bb50f9c3122ec844ad7c2b3e5")
        OKM = unhexlify(b"3cb25f25faacd57a90434f64d0362f2a") +\
              unhexlify(b"2d2d0a90cf1a5a4c5db02d56ecc4c5bf") +\
              unhexlify(b"34007208d5b887185865")
        self.assertEquals(HKDF_extract(salt, IKM, hashmod), PRK)
        self.assertEquals(HKDF(IKM, salt, info, L, hashmod), OKM)

    def test_hkdf_rfc_case7(self):
        hashmod = hashlib.sha1
        IKM = unhexlify(b"0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c")
        salt = None
        info = b""
        L = 42
        PRK = unhexlify(b"2adccada18779e7c2077ad2eb19d3f3e731385dd")
        OKM = unhexlify(b"2c91117204d745f3500d636a62f64f0a") +\
              unhexlify(b"b3bae548aa53d423b0d1f27ebba6f5e5") +\
              unhexlify(b"673a081d70cce7acfc48")
        self.assertEquals(HKDF_extract(salt, IKM, hashmod), PRK)
        self.assertEquals(HKDF(IKM, salt, info, L, hashmod), OKM)
