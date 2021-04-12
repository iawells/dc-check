import unittest
import click
import logging
import os
import os.path

import dc_check.server

DIR = os.path.dirname(os.path.abspath(__file__))


class TestWebserverBasic(unittest.TestCase):
    """Test of the flask app"""

    db_file = os.path.join(DIR, "loader", "valid.yaml")

    def setUp(self) -> None:
        # TODO(ijw): unitttest and files
        try:
            os.unlink(self.db_file)
        except FileNotFoundError:
            pass

        self.app = dc_check.server.create_app(self.db_file).test_client()

    def test_index(self) -> None:
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        print(type(res))
        self.assertIn('dc-check', res.data.decode('utf-8'))

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_file)
        except FileNotFoundError:
            pass
