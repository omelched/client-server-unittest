import socketserver
from unittest import TestCase
import os
import threading
import time

os.environ['UNIT_TESTS_IN_PROGRESS'] = '1'

from server import network, message

_CHUNK_SIZE = 1024
_VERSION = '0.0.1'
_SESSION = 12345


class ProxyServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.data = []


class ProxyRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = str(self.request.recv(_CHUNK_SIZE), 'utf-8')
        self.server.data.append(data)


class TestBlankServerClass(object):
    version = _VERSION


class SessionClass_tests(TestCase):

    def test_regenerate_hash_trace(self):
        self.session_class_instance = network.SessionClass(network.ConnectionClass([None]))
        self.session_class_instance.id = _SESSION
        self.session_class_instance.regenerate_hash_trace(_VERSION)
        self.assertEqual('1c021062b3', self.session_class_instance.hash_trace)


class Server_tests(TestCase):

    def tearDown(self) -> None:
        try:
            self.test_server_obj.server_close()
            self.listener_server.server_close()
        except Exception as e:
            print(e)

    def test_Server_send_message(self):
        self.test_server_obj = network.Server(('localhost', 45890),
                                              network.ThreadedTCPRequestHandler,
                                              network.MessageProcessor,
                                              network.ServerExecutor)

        test_message = message.OutputMessage((_SESSION, _VERSION, _CHUNK_SIZE), body=('ping_pong', 'test_msg'))
        self.listener_server = ProxyServer(('localhost', 45891), ProxyRequestHandler)
        self.listener_server.server_thread = threading.Thread(target=self.listener_server.serve_forever)
        self.listener_server.server_thread.daemon = True
        self.listener_server.server_thread.start()
        self.test_server_obj.send_message(('localhost', 45891), test_message)
        time.sleep(.001)
        self.assertEqual([i for i in test_message.encode()], self.listener_server.data)

        time.sleep(.001)

