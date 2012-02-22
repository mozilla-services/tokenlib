# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import unittest2
import tempfile
import os

from tokenlib.secrets import Secrets


class TestSecrets(unittest2.TestCase):

    def setUp(self):
        self._files = []

    def tearDown(self):
        for file in self._files:
            if os.path.exists(file):
                os.remove(file)

    def tempfile(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        self._files.append(path)
        return path

    def test_read_write(self):
        secrets = Secrets()

        secrets.add('phx23456')
        secrets.add('phx23456')
        secrets.add('phx23')

        phx23456_secrets = secrets.get('phx23456')
        self.assertEqual(len(secrets.get('phx23456')), 2)
        self.assertEqual(len(secrets.get('phx23')), 1)

        path = self.tempfile()

        secrets.save(path)

        secrets2 = Secrets(path)
        self.assertEqual(len(secrets2.get('phx23456')), 2)
        self.assertEqual(len(secrets2.get('phx23')), 1)
        self.assertEquals(secrets2.get('phx23456'), phx23456_secrets)
