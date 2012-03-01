# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
from unittest2 import TestCase
import os
from tokenlib.metadata.sql import SQLMetadata


_SQLURI = 'sqlite:////tmp/tokenserver'


class TestLDAPNode(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()

        self.backend = SQLMetadata(_SQLURI, create_tables=True)

        # adding a node with 100 slots
        self.backend._safe_execute(
              """insert into nodes (`node`, `service`, `available`,
                    `capacity`, `current_load`, `downed`, `backoff`)
                  values ("phx12", "sync", 100, 100, 0, 0, 0)""")

        self._sqlite = self.backend._engine.driver == 'pysqlite'

    def tearDown(self):
        if self._sqlite:
            filename = self.backend.sqluri.split('sqlite://')[-1]
            if os.path.exists(filename):
                os.remove(filename)
        else:
            self.backend._safe_execute('delete from nodes')
            self.backend._safe_execute('delete from user_nodes')

    def test_get_node(self):

        unassigned = None, None
        self.assertEquals(unassigned,
                          self.backend.get_node("tarek@mozilla.com", "sync"))

        res = self.backend.allocate_node("tarek@mozilla.com", "sync")

        if self._sqlite:
            wanted = (1, u'phx12')
        else:
            wanted = (0, u'phx12')

        self.assertEqual(res, wanted)
        self.assertEqual(wanted,
                         self.backend.get_node("tarek@mozilla.com", "sync"))
