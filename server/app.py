import threading

from server.message import OutputMessage
from server.server_class import ServerThreadedTCPRequestHandler, MessageProcessor, ServerExecutor, Server

HOST, PORT = 'localhost', 15151


class ServerApp(object):
    def __init__(self, settings):
        self.HOST, self.PORT = settings[0], settings[1]

        self.server = Server((HOST, PORT),
                             ServerThreadedTCPRequestHandler,
                             MessageProcessor,
                             ServerExecutor)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        # self.interface_loop()

    def interface_loop(self):
        self.server_thread.start()
        print('Server loop running in thread:', self.server_thread.name)
        print("Доступные команды:\n\tlist: — показать список подсоединённых клиентов\n\tq: — выключить программу\n"
              "\tstop: — выключить программу")
        while True:
            input_line = input().split(':')
            cmd = input_line[0]
            if cmd == 'stop':
                self.server.shutdown()
            elif cmd == 'q':
                try:
                    self.server.shutdown()
                except Exception as e:
                    print(e)
                exit()
            elif cmd == 'list':
                print(self.server.session_list)
            else:
                print('wrong cmd')
