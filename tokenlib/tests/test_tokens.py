# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import hashlib
import time
import warnings

if sys.version_info < (2, 7):
    import unittest2 as unittest  # pragma: nocover
else:
    import unittest  # pragma: nocover  # NOQA

import tokenlib
from tokenlib.utils import encode_token_bytes


class TestTokens(unittest.TestCase):

    def test_token_validation(self):
        manager = tokenlib.TokenManager(timeout=0.2)
        token = manager.make_token({"hello": "world"})
        # Proper token == valid.
        data = manager.parse_token(token)
        self.assertEquals(data["hello"], "world")
        # Bad signature == not valid.
        bad_token = token[:-1] + ("X" if token[-1] == "Z" else "Z")
        self.assertRaises(ValueError, manager.parse_token, bad_token)
        bad_token = encode_token_bytes(b"X" * 50)
        self.assertRaises(ValueError, manager.parse_token, bad_token)
        # Modified payload == not valid.
        bad_token = "admin" + token[6:]
        self.assertRaises(ValueError, manager.parse_token, bad_token)
        # Expired token == not valid.
        time.sleep(0.2)
        self.assertRaises(ValueError, manager.parse_token, token)

    def test_loading_hashmod_by_string_name(self):
        manager = tokenlib.TokenManager(hashmod="md5")
        self.assertTrue(manager.hashmod is hashlib.md5)

    def test_token_secrets_differ_for_each_token(self):
        manager = tokenlib.TokenManager()
        token1 = manager.make_token({"test": "one"})
        token2 = manager.make_token({"test": "two"})
        self.assertEquals(manager.get_derived_secret(token1),
                          manager.get_derived_secret(token1))
        self.assertNotEquals(manager.get_derived_secret(token1),
                             manager.get_derived_secret(token2))

    def test_tokens_differ_for_different_master_secrets(self):
        manager1 = tokenlib.TokenManager(secret="one")
        manager2 = tokenlib.TokenManager(secret="two")
        token1 = manager1.make_token({"test": "data"})
        token2 = manager2.make_token({"test": "data"})
        self.assertNotEquals(token1, token2)
        self.assertNotEquals(manager1.get_derived_secret(token1),
                             manager2.get_derived_secret(token2))
        self.assertRaises(ValueError, manager1.parse_token, token2)
        self.assertRaises(ValueError, manager2.parse_token, token1)

    def test_get_derived_secret_errors_out_for_malformed_tokens(self):
        manager = tokenlib.TokenManager()
        digest_size = manager.hashmod_digest_size
        bad_token = encode_token_bytes(b"{}" + (b"X" * digest_size))
        self.assertRaises(ValueError, manager.get_derived_secret, bad_token)
        bad_token = encode_token_bytes(b"42" + (b"X" * digest_size))
        self.assertRaises(ValueError, manager.get_derived_secret, bad_token)
        bad_token = encode_token_bytes(b"NOTJSON" + (b"X" * digest_size))
        self.assertRaises(ValueError, manager.get_derived_secret, bad_token)

    def test_master_secret_can_be_unicode_string(self):
        manager = tokenlib.TokenManager(secret=b"one".decode("ascii"))
        token = manager.make_token({"test": "data"})
        self.assertEquals(manager.parse_token(token)["test"], "data")

    def test_convenience_functions(self):
        token = tokenlib.make_token({"hello": "world"})
        self.assertEquals(tokenlib.parse_token(token)["hello"], "world")
        self.assertRaises(ValueError, tokenlib.parse_token, token, secret="X")
        self.assertEquals(tokenlib.get_derived_secret(token),
                          tokenlib.get_derived_secret(token))
        self.assertNotEquals(tokenlib.get_derived_secret(token),
                             tokenlib.get_derived_secret(token, secret="X"))

    def test_tokens_are_native_string_type(self):
        token = tokenlib.make_token({"hello": "world"})
        assert isinstance(token, str)

    def test_get_token_secret_is_deprecated(self):
        token = tokenlib.make_token({"hello": "world"})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("default")
            tokenlib.get_token_secret(token)
            self.assertEquals(len(w), 1)
            self.assertEquals(w[0].category, DeprecationWarning)
