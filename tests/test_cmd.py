import unittest
import click
import logging

from click.testing import CliRunner
from dc_check.server_cmd import main


class TestServerCmd(unittest.TestCase):
    """Basic tests of the server click entrypoint"""

    def test_noargs(self) -> None:
        runner = CliRunner()

        result = runner.invoke(main)
        self.assertEqual(result.exit_code, 1)
