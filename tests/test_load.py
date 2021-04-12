import unittest
from parameterized import parameterized
import os.path
import glob

from typing import List, Optional, Tuple

from dc_check.rack.load import NotValid, read_server_file
# from .rack.pprint import dump_conns_by_rack_and_device


DIR = os.path.dirname(os.path.abspath(__file__))


def rchop(s: str, suffix: str) -> str:
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def glob_tests() -> List[Tuple[str, str, str]]:
    results = []
    for input_file in glob.glob(os.path.join(DIR, 'loader', '*.yaml')):
        base_name = rchop(input_file, '.yaml')
        err_file = base_name + '.err'

        if os.path.exists(err_file):
            with open(err_file) as err_f:
                expected_errs = err_f.read().strip()
        else:
            expected_errs = ''

        results.append((os.path.basename(base_name),
                        input_file,
                        expected_errs,))

    return results


class TestRackDescriptionLoader(unittest.TestCase):
    maxDiff = 10000

    # parameterized is not mypy-friendly
    @parameterized.expand(glob_tests())  # type: ignore
    def test_load(self, name: str, input_file: str,
                  expected_errs: str) -> None:

        try:
            server_file_data = read_server_file(input_file)

            # print(f'{filename}: connections by device:')
            # dump_conns_by_rack_and_device(server_file_data)

            # We expect no errors if it threw no exception
            errs = ''
        except NotValid as e:
            errs = e.msg.strip()

        self.assertMultiLineEqual(expected_errs, errs)
