# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import csv
import binascii
import os
import time
from collections import defaultdict

# XXX we don't watch the file for v1
# so a restart is needed to reload new secrets


class Secrets(object):
    """ Loads into memory a secret file, and provide a method
    to get a list of secrets for a node, ordered by timestamps
    """
    def __init__(self, filename=None):
        self._secrets = defaultdict(list)
        self.filename = None
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        if self.filename is not None:
            raise ValueError('Already loaded')

        self._filename = filename
        with open(filename, 'rb') as f:

            reader = csv.reader(f, delimiter=',')
            for line, row in enumerate(reader):
                if len(row) < 2:
                    continue
                node = row[0]
                if node in self._secrets:
                    raise ValueError("Duplicate node line %d" % line)
                secrets = []
                for secret in row[1:]:
                    secret = secret.split(':')
                    if len(secret) != 2:
                        raise ValueError("Invalid secret line %d" % line)
                    secrets.append(tuple(secret))
                secrets.sort()
                self._secrets[node] = secrets

    def save(self, filename=None):
        if filename is None:
            filename = self._filename
        if filename is None:
            raise ValueError('You need to provide a filename')

        with open(filename, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            for node, secrets in self._secrets.items():
                secrets = ['%s:%s' % (timestamp, secret)
                           for timestamp, secret in secrets]
                secrets.insert(0, node)
                writer.writerow(secrets)

    def get(self, node):
        return [secret for timestamp, secret in self._secrets[node]]

    def add(self, node, size=256):
        timestamp = str(int(time.time()))
        secret = binascii.b2a_hex(os.urandom(size))[:size]
        self._secrets[node].insert(0, (timestamp, secret))
