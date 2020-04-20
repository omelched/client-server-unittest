import threading
import unittest
import socket
import subprocess
import sys
import os
import time
import socketserver

_CHUNK_SIZE = 1024
_VERSION = '0.0.1'
_SESSION = 12345

from server import utils, server_class, message


# sys.path.append('/Users/user/PycharmProjects/server-app/server')

class TestServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.data = []


class TestRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(_CHUNK_SIZE), 'utf-8')
        self.server.data.append(data)


def run_in_subproc(filepath):
    abs_path = os.path.abspath(filepath)
    cmd = ['python', abs_path]
    p = subprocess.check_output(['python', '/Users/user/PycharmProjects/server-app/server/test_ServerExecutor_svr_print.py'])
    print(p)


class UtilsTests(unittest.TestCase):
    def test_ut8len(self):
        self.assertEqual(33, utils.utf8len('this string is XX characters long'))

    def test_parse_string(self):
        self.assertEqual(['this', 'is', 'test', 'string'], utils.parse_string('this=is=test=string'))

    def test_get_hash(self):
        self.assertEqual('1c021062b3fbe06635aa91a343e176baec1e4946', utils.get_hash(_SESSION, _VERSION))


class ServerClassTests(unittest.TestCase):

    def test_Server_send_message(self):
        self.test_server_obj = server_class.Server(('localhost', 8080),
                                                   server_class.ServerThreadedTCPRequestHandler,
                                                   server_class.MessageProcessor,
                                                   server_class.ServerExecutor)

        test_message = message.OutputMessage((_SESSION, _VERSION, _CHUNK_SIZE), body=('ping_pong', 'test_msg'))
        listener_server = TestServer(('localhost', 8081), TestRequestHandler)
        listener_server.server_thread = threading.Thread(target=listener_server.serve_forever)
        listener_server.server_thread.daemon = True
        listener_server.server_thread.start()
        self.test_server_obj.send_message(('localhost', 8081), test_message)
        time.sleep(.001)
        self.assertEqual([i for i in test_message.encode()], listener_server.data)
        self.test_server_obj.server_close()
        del self.test_server_obj
        listener_server.server_close()
        del listener_server
        time.sleep(.001)

    # def test_ServerThreadedTCPRequestHandler_handle(self):
    #     self.test_server_obj = server_class.Server(('localhost', 8080),
    #                                                server_class.ServerThreadedTCPRequestHandler,
    #                                                server_class.MessageProcessor,
    #                                                server_class.ServerExecutor)
    #
    #     test_message = message.OutputMessage((_SESSION, _VERSION, _CHUNK_SIZE), body=('test_cmd', 'test_msg'))
    #     listener_server = TestServer(('localhost', 8081), TestRequestHandler)
    #     listener_server.server_thread = threading.Thread(target=listener_server.serve_forever)
    #     listener_server.server_thread.daemon = True
    #     listener_server.server_thread.start()
    #     for msg in test_message.encode():
    #         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    #             sock.connect(('localhost', 8080))
    #             sock.sendall(bytes(msg, 'utf-8'))
    #             print("sent {}".format(msg))
    #             sock.close()
    #     time.sleep(.001)

    def test_ServerExecutor_svr_print(self):
        file_path = 'test_ServerExecutor_svr_print.py'
        script = \
            """#!/usr/bin/env python
print(\'test\')
"""
        file = open(file_path, 'w+')
        file.truncate(0)
        file.write(script)
        print(run_in_subproc(file_path))
        file.close()
        # os.remove(file_path)
# calcTestSuite = unittest.TestSuite()
# calcTestSuite.addTest(unittest.makeSuite(calc_tests.CalcBasicTests))
# calcTestSuite.addTest(unittest.makeSuite(calc_tests.CalcExTests))
# print("count of tests: " + str(calcTestSuite.countTestCases()) + "\n")
#
# runner = unittest.TextTestRunner(verbosity=2)
# runner.run(calcTestSuite)
