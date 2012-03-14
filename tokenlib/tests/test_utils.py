# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib
import unittest2

from tokenlib.utils import strings_differ, HKDF, HKDF_extract


class TestUtils(unittest2.TestCase):

    def test_strings_differ(self):
        # We can't really test the timing-invariance, but
        # we can test that we actually compute equality!
        self.assertTrue(strings_differ("", "a"))
        self.assertTrue(strings_differ("b", "a"))
        self.assertTrue(strings_differ("cc", "a"))
        self.assertTrue(strings_differ("cc", "aa"))
        self.assertFalse(strings_differ("", ""))
        self.assertFalse(strings_differ("D", "D"))
        self.assertFalse(strings_differ("EEE", "EEE"))

    def test_hkdf_rfc_case1(self):
        hashmod = hashlib.sha256
        IKM = "0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b".decode("hex")
        salt = "000102030405060708090a0b0c".decode("hex")
        info = "f0f1f2f3f4f5f6f7f8f9".decode("hex")
        L = 42
        PRK = "077709362c2e32df0ddc3f0dc47bba63".decode("hex") +\
              "90b6c73bb50f9c3122ec844ad7c2b3e5".decode("hex")
        OKM = "3cb25f25faacd57a90434f64d0362f2a".decode("hex") +\
              "2d2d0a90cf1a5a4c5db02d56ecc4c5bf".decode("hex") +\
              "34007208d5b887185865".decode("hex")
        self.assertEquals(HKDF_extract(salt, IKM, hashmod), PRK)
        self.assertEquals(HKDF(IKM, salt, info, L, hashmod), OKM)

    def test_hkdf_rfc_case7(self):
        hashmod = hashlib.sha1
        IKM = "0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c".decode("hex")
        salt = None
        info = ""
        L = 42
        PRK = "2adccada18779e7c2077ad2eb19d3f3e731385dd".decode("hex")
        OKM = "2c91117204d745f3500d636a62f64f0a".decode("hex") +\
              "b3bae548aa53d423b0d1f27ebba6f5e5".decode("hex") +\
              "673a081d70cce7acfc48".decode("hex")
        self.assertEquals(HKDF_extract(salt, IKM, hashmod), PRK)
        self.assertEquals(HKDF(IKM, salt, info, L, hashmod), OKM)
