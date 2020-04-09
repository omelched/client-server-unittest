import threading

from client.message import OutputMessage
from client.client import Client, ClientThreadedTCPRequestHandler, MessageProcessor, ClientExecutor


class ClientApp(object):
    def __init__(self, settings):
        self.HOST, self.PORT = settings[0], settings[1]
        self.srv_HOST, self.srv_PORT = 'localhost', 15151
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
        self.client.send_message((self.srv_HOST, self.srv_PORT), init_msg)

    def _interface_loop(self):
        print("Доступные команды:\n\ts: {{string}} — напечатать на сервере строку \n\tq: — выключить программу")
        while True:
            input_line = input().split(':')
            cmd = input_line[0]
            if cmd == 's':
                test = OutputMessage((self.session, '0.1', 1024), ('svr_print', input_line[1]))
                self.client.send_message((self.srv_HOST, self.srv_PORT), test)
            elif cmd == 'q':
                self.client.server_close()
                exit()
            else:
                print('wrong cmd')
