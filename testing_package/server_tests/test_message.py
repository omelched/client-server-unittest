from unittest import TestCase
import os

os.environ['UNIT_TESTS_IN_PROGRESS'] = '1'

from server import message

_CHUNK_SIZE = 1024
_VERSION = '0.0.1'
_SESSION = 12345


class OutputMessage_tests(TestCase):

    def setUp(self) -> None:
        self.message = message.OutputMessage((_SESSION, _VERSION, _CHUNK_SIZE),
                                             ('test_cmd', 'test_msg'))

    def test_encode(self):
        golden_list = ['1c021062b3fbe06635aa91a343e176baec1e4946:23|56|50|23|',
                       '1c021062b3:cmd=test_cmd',
                       '1c021062b3:hash=1c021062b3fbe06635aa91a343e176baec1e4946',
                       '1c021062b3:id=d9b83296-76e8-4b67-b775-bf4c7338056f',
                       '1c021062b3:msg=test_msg',
                       '1c021062b3fbe06635aa:EOF']
        for i, elem in enumerate(golden_list):
            if '1c021062b3:id=' in elem:
                del golden_list[i]

        msg_output = self.message.encode()
        for i, elem in enumerate(msg_output):
            if '1c021062b3:id=' in elem:
                del msg_output[i]

        self.assertEqual(golden_list, msg_output)
