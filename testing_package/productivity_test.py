import os
import time
import socketserver
import threading
import unittest
from random import choice
from string import ascii_uppercase

os.environ['UNIT_TESTS_IN_PROGRESS'] = '1'

from client import app, network
from client.message import OutputMessage
from server import app as s_app

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


class ProductivityTests(unittest.TestCase):
    def setUp(self) -> None:
        while True:
            try:
                self.test_message = OutputMessage((app.session, '0.1', 1024), ('svr_print', 'TESTING'))
                self.application = app

                self.application.client.server_adr = ('localhost', 45891)
                self.listener_server = ProxyServer(('localhost', 45891), ProxyRequestHandler)
                self.listener_server.server_thread = threading.Thread(target=self.listener_server.serve_forever)
                self.listener_server.server_thread.daemon = True
                self.listener_server.server_thread.start()
                time.sleep(.1)
                self.application.init_on_server()
                time.sleep(.1)
                self.listener_server.data.clear()
                time.sleep(.1)
                break
            except OSError:
                time.sleep(2)
                print('Wait 2 more sec to flush')
                continue

    def test_message_density(self, start_delay_ms: float = 10000000.0, ratio: float = .5, min_delay_ms=5.0):

        delay = start_delay_ms
        message_to_list = [i for i in self.test_message.encode()]
        while delay > min_delay_ms:
            print('тестируем с задержкой {}'.format(delay))
            self.application.client.send_message(self.test_message)
            time.sleep(delay / 1000000.0)
            check_value = self.listener_server.data
            try:
                self.assertListEqual(message_to_list, check_value)
            except AssertionError:
                print('Не справились на delay={} мс\n с ошибкой'.format(delay))
                print(message_to_list)
                print(check_value)
                break
            print('Успешно справились на delay={} мс'.format(delay))
            delay *= ratio
            self.listener_server.data.clear()

        self.application.client.shutdown()
        self.listener_server.shutdown()
        print('Тестирование завершено')

    def test_message_volume(self, start_volume: int = 900, ratio: int = 2, max_volume: int = 1048576):

        volume = start_volume

        while volume < max_volume:
            self.test_message = OutputMessage((app.session, '0.1', 1024),
                                              ('svr_print', ''.join(choice(ascii_uppercase) for _ in range(volume))))
            message_to_list = [i for i in self.test_message.encode()]
            print('тестируем отправку сообщения размером {} байт'.format(volume))
            self.application.client.send_message(self.test_message)
            time.sleep(.1)
            check_value = self.listener_server.data
            try:
                self.assertListEqual(message_to_list, check_value)
            except AssertionError:
                print('Не справились на volume={} байт\n с ошибкой'.format(volume))
                print(message_to_list)
                print(check_value)
                break
            print('Успешно справились на volume={} байт'.format(volume))
            volume *= ratio
            self.listener_server.data.clear()

        self.application.client.shutdown()
        self.listener_server.shutdown()
        print('Тестирование завершено')


if __name__ == '__main__':
    pt = ProductivityTests()
    unittest.main()
