import threading
import time

from client.message import OutputMessage
from client.network import Client, ClientThreadedTCPRequestHandler, MessageProcessor, ClientExecutor


class ClientApp(object):
    def __init__(self, settings):
        self.HOST, self.PORT = settings[0], settings[1]
        self.session = 0

        self.client = Client(self, (self.HOST, self.PORT),
                             ClientThreadedTCPRequestHandler,
                             MessageProcessor,
                             ClientExecutor)
        self.client_thread = threading.Thread(target=self.client.serve_forever)
        self.client_thread.daemon = True

        self.client_thread.start()

        self._init_on_server()

        self._interface_loop()

    def _init_on_server(self):
        init_msg = OutputMessage((self.session, self.client.version, self.client.chunk_size),
                                 ('initialize_session', '{}:{}'.format(self.HOST, self.PORT)))
        self.client.send_message(init_msg)

    def _delete_on_server(self):
        delete_msg = OutputMessage((self.session, self.client.version, self.client.chunk_size),
                                   ('delete_session', self.session))
        self.client.send_message(delete_msg)

    def _close_app(self):
        timeout = 10
        try:
            self._delete_on_server()
            timeout_start = time.time()
            while time.time() < timeout_start + timeout and not self.client.killed_on_server:
                print('we are waiting')
                time.sleep(1)
        except ConnectionRefusedError:
            pass
        self.client.server_close()
        exit()

    def _interface_loop(self):
        print("Доступные команды:\n\ts: {{string}} — напечатать на сервере строку \n\tq: — выключить программу")
        while True:
            input_line = None
            try:
                input_line = input().split(':')
            except KeyboardInterrupt:
                self._close_app()
                exit()
            except Exception as e:
                self._close_app()
                raise e
            cmd = input_line[0]
            if cmd == 's':
                test = OutputMessage((self.session, '0.1', 1024), ('svr_print', input_line[1]))
                self.client.send_message(test)
            elif cmd == 'sd':
                test = OutputMessage((self.session, '0.1', 1024), ('svr_print', input_line[1]))
                self.client.send_message(test, DEBUG=True)
            elif cmd == 'q':
                self._close_app()
            else:
                print('wrong cmd')
