"""
Подсистема server - подсистема серверного взаимодейтсвия
Подразделяется на 5 классов:

Client - класс клиента
ConfigClass - класс настроек сервера
ThreadedTCPRequestHandler - класс Обработчиков входящих запросов
MessageProcessor — класс Процессоров полученных соединений
ServerExecutor - класс Исполнителей полученных команд
ConnectionClass - класс установленных соединений
"""

import socket
import socketserver

from client.message import InputMessage, OutputMessage
from client.utils import parse_string


class ConfigClass(object):
    """
    ConfigClass - класс настроек клиента.
    Содержит константы и/или настройки для работы клиента.
    Не инстанциируется непосредственно - лишь является одним из родителей класса Server.
    """

    def __init__(self):
        """
        Метод инициализации.
        Устанавливаются некоторые предопределенные значения.
        """

        self.version = '0.1'
        self.small_cache_size = 10
        self.chunk_size = 1024
        self.server_adr = ('localhost', 15151)


class Client(socketserver.ThreadingTCPServer, ConfigClass):
    """
    Client - класс клиента.
    """

    def __init__(self,
                 app,
                 client_address: tuple,
                 RequestHandlerClass,
                 MessageProcessorClass,
                 ClientExecutorClass):
        """
        Метод инициализации.
        Отрабатывают функции инициализации родителей,
        создаёт пустой список для открытых соединений,
        инстанциируются Процессор сообщений и Исполнитель сообщений.
        Создаются буфера активных соединений и сообщений, ожидающих ответа.

        :param app: экземпляр класса ClientApp для работы которого инстанциируется клиент
        :param client_address: кортеж (IP: string, PORT: int)
        :param RequestHandlerClass: Класс Обработчика входящих запросов (для последующей инстанциации)
        :param MessageProcessorClass: Класс Процессора полученных соединений (для последующей инстанциации)
        :param ClientExecutorClass: Класс Исполнителя полученных команд (для последующей инстанциации)
        """

        self.app = app
        super().__init__(client_address, RequestHandlerClass)
        ConfigClass.__init__(self)
        self.msg_proc = MessageProcessorClass(self)
        self.executor = ClientExecutorClass(self)
        self.open_conn = []
        self.pending_messages = []

    def send_message(self, message: OutputMessage):
        """
        Метод отправки сообщения серверу.

        :param message: сообщение - объект класса OutputMessage
        """

        for msg in message.encode():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_adr[0], self.server_adr[1]))
                sock.sendall(bytes(msg, 'utf-8'))
                print("sent {}".format(msg))
                sock.close()
        self.pending_messages.append(message.id)


class ConnectionClass(object):
    """
    ConnectionClass — класс установленных соединений между приложениями.
    """

    def __init__(self, session_hash: str, size_list: list):
        """
        Инстанциируется при приеме первого запроса от другого приложения,
        в процессе получения остаточных запросов -  наполняется информацией,
        уничтожается в результате Процессинга.

        :param session_hash: входящий хэш сеанса (для проверки актуальности версий и поиска уже открытых сеансов)
        :param size_list: массив из boolean, определяющий превышает ли закодированная информация в сообщении буфер
        TCP-соединения. Если превышает (True) - то информация будет выслана несколькими запросами, следовательно
        нужно грамотно декодировать во время Обработки.
        """

        self.hash_trace = session_hash[:10]
        self.size_list = size_list
        self.data = []


class MessageProcessor(object):
    """
    MessageProcessor - класс процессоров полученных соединений.
    Инстанцируется при запуске сервера.
    Восстанавливает сообщения из соединений, полученных при обработке входящих запросов.
    """

    def __init__(self, client_instance: Client):
        """
        Метод инициализации объекта.
        :param client_instance: объект класса Client для работы которого инстанциируется Процессор полученных соединений
        """

        self.client = client_instance

    def process_response(self, connection: ConnectionClass):
        """
        Метод процессинга ответного соединения.
        Создает экземпляр класса InputMessage с данными из ответного
        соединения сервера.
        Удаляет сообщение из списка необработанных сообщений.

        :param connection: экземпляр класса
        ConnectionClass — установленное соединение, которое необходимо от-Процессить.
        """

        input_params = []
        for key_value in connection.data:
            input_params.append(parse_string(key_value))
        message = InputMessage(self.client.chunk_size, input_params)
        if message.id in self.client.pending_messages:
            self.execute_message(message)
            self.client.pending_messages.remove(message.id)

    def execute_message(self, message: InputMessage):
        """
        Метод проверки и исполнения команды из ответа сервера.
        Устанавливает соответствие между командой входящего сообщения
        и методом экземпляра Исполнителя полученных команд.

        :param message: экземпляр класса InputMessage — сообщение, которое содержит исполняемую команду
        """

        cmd = getattr(message, 'cmd')
        if cmd in getattr(self.client.executor, '_get_available_commands')():
            try:
                getattr(self.client.executor, cmd)(message)
            except Exception as e:
                raise e
        else:
            print('Client command {} not available'.format(cmd))


class ClientExecutor(object):
    """
    ClientExecutor - класс Исполнителей полученных команд.
    Исполняет команды, полученные от других приложений.
    Доступные команды представляют собой публичные методы этого класса.

    Новая команда должна добавляться объявлением соответствующего метода, для которого единственным аргументом будет
    экземпляр класса InputMessage!
    """

    def __init__(self, client_instance: Client):
        """
        Метод инициализации объекта.

        :param client_instance: объект класса Client для работы которого инстанциируется Исполнитель полученных команд.
        """

        self.client = client_instance

    @staticmethod
    def clt_print(message: InputMessage):
        print(message.msg)

    def approve_init(self, message: InputMessage):
        self.client.app.session = int(message.msg)

    @staticmethod
    def svr_approve(message: InputMessage):
        print('Server successfully executed command {}!'.format(message.msg))

    def _get_available_commands(self):
        return [key for key in [s for s in dir(self) if s[:1] != '_' and callable((getattr(self, s)))]]


class ClientThreadedTCPRequestHandler(socketserver.BaseRequestHandler):  # заточить на работу с одним сервером

    def handle(self):
        """
        Метод handle вызывается как только клиент получает ответ от сервера.
        """

        data = str(self.request.recv(self.server.chunk_size), 'utf-8')
        if not self.client_address == self.server.server_adr:
            print('got {} from not our server {}'.format(data, self.client_address))
            return
        print("got {} from {}".format(data, self.client_address))
        session_hash = data.split(':')[0]

        if len(session_hash) == 40:
            size_list = [True if int(i) > self.server.chunk_size else False for i in
                         data.split(':')[1][:-1].split('|')[:-1]]
            size_list.insert(0, False)
            connection = ConnectionClass(session_hash, size_list)
            self.server.open_conn.append(connection)

        elif len(session_hash) == 20:
            for connection in self.server.open_conn:
                if session_hash[:10] == connection.hash_trace:
                    self.server.open_conn.remove(connection)
                    self.server.msg_proc.process_response(connection)
                else:
                    print('InvalidConnection! Failed to remove {}'.format(session_hash))

        elif len(session_hash) == 10:
            for connection in self.server.open_conn:
                if session_hash == connection.hash_trace:
                    if not connection.size_list[len(connection.data)]:
                        connection.data.append(data.split(':', 1)[1])
                    else:
                        connection.data[-1] += data.split(':', 1)[1]
                else:
                    print('InvalidConnection! Failed to update {}'.format(session_hash))
