"""
Подстема app - подсистема работы приложения

ServerApp - класс приложениия.

"""
import threading
from server.network import ThreadedTCPRequestHandler, MessageProcessor, ServerExecutor, Server

HOST, PORT = 'localhost', 15151


class ServerApp(object):
    """
    ServerApp - класс приложений.
    Экземпляр этого класса является непосредственно приложением, производящим общение с пользователем.
    """
    def __init__(self):
        """
        Метод инициализации.
        Сохраняет в память на каком сервере и порте запускается.
        Инстанциирует класс Server.
        Создает thread перехвата входящих TCP-запросов, но не запускает его.
        """

        self.server = Server((HOST, PORT),
                             ThreadedTCPRequestHandler,
                             MessageProcessor,
                             ServerExecutor)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def interface_loop(self):
        """
        Метод запуска интерфейса приложения.
        Запускает thread перехвата входящих TCP-запросов.
        Отображает пользователю доступные команды и ждет их ввода.
        :return:
        """
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
