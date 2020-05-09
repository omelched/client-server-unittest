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

from server import utils, network, message


class TestServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.data = []


class TestRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(_CHUNK_SIZE), 'utf-8')
        self.server.data.append(data)


class UtilsTests(unittest.TestCase):
    def test_ut8len(self):
        self.assertEqual(33, utils.utf8len('this string is XX characters long'))

    def test_parse_string(self):
        self.assertEqual(['this', 'is', 'test', 'string'], utils.parse_string('this=is=test=string'))

    def test_get_hash(self):
        self.assertEqual('1c021062b3fbe06635aa91a343e176baec1e4946', utils.get_hash(_SESSION, _VERSION))
#
#
# class ServerClassTests(unittest.TestCase):
#
#     def test_Server_send_message(self):
#         self.test_server_obj = network.Server(('localhost', 8080),
#                                               network.ThreadedTCPRequestHandler,
#                                               network.MessageProcessor,
#                                               network.ServerExecutor)
#
#         test_message = message.OutputMessage((_SESSION, _VERSION, _CHUNK_SIZE), body=('ping_pong', 'test_msg'))
#         listener_server = TestServer(('localhost', 8081), TestRequestHandler)
#         listener_server.server_thread = threading.Thread(target=listener_server.serve_forever)
#         listener_server.server_thread.daemon = True
#         listener_server.server_thread.start()
#         self.test_server_obj.send_message(('localhost', 8081), test_message)
#         time.sleep(.001)
#         self.assertEqual([i for i in test_message.encode()], listener_server.data)
#         self.test_server_obj.server_close()
#         del self.test_server_obj
#         listener_server.server_close()
#         del listener_server
#         time.sleep(.001)
