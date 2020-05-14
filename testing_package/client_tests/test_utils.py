from unittest import TestCase
import os

os.environ['UNIT_TESTS_IN_PROGRESS'] = '1'

from client import utils


class UtilsTests(TestCase):

    def setUp(self) -> None:
        self.test_SESSION = 12345
        self.test_VERSION = '0.0.1'

    def test_ut8len(self):
        self.assertEqual(33, utils.utf8len('this string is XX characters long'))

    def test_parse_string(self):
        self.assertEqual(['this', 'is', 'test', 'string'], utils.parse_string('this=is=test=string'))

    def test_get_hash(self):
        self.assertEqual('1c021062b3fbe06635aa91a343e176baec1e4946', utils.get_hash(self.test_SESSION,
                                                                                    self.test_VERSION))
