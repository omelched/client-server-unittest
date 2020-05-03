"""
Подсистема network - подсистема сетевого взаимодейтсвия
Подразделяется на 5 классов:

Server - класс серверного взаимодействия
ConfigClass - класс настроек сервера
ThreadedTCPRequestHandler - класс Обработчиков входящих запросов
MessageProcessor — класс Процессоров полученных соединений
ServerExecutor - класс Исполнителей полученных команд
ConnectionClass - класс установленных соединений
"""

import socket
import socketserver

from server.message import InputMessage, OutputMessage
from server.utils import get_hash, parse_string


class ConfigClass(object):
    """
    ConfigClass - класс настроек сервера.
    Содержит константы и/или настройки для работы сервера.
    Не инстанциируется непосредственно - лишь является одним из родителей класса Server.
    """

    def __init__(self):
        """
        Метод инициализации.
        Устанавливаются некоторые предопределенные значения.
        """
        self.version = '0.1'
        self.session_list = {}
        self.small_cache_size = 10
        self.chunk_size = 1024


class Server(socketserver.ThreadingTCPServer, ConfigClass):
    """
    Server - класс серверного взаимодействия.
    """

    def __init__(self, server_address: tuple, RequestHandlerClass, MessageProcessorClass, ServerExecutorClass):
        """
        Метод инициализации.
        Отрабатывают функции инициализации родителей,
        создаёт пустой список для открытых соединений,
        инстанциируются Процессор сообщений и Исполнитель сообщений.

        :param server_address: кортеж (IP: string, PORT: int)
        :param RequestHandlerClass: Класс Обработчика входящих запросов (для последующей инстанциации)
        :param MessageProcessorClass: Класс Процессора полученных соединений (для последующей инстанциации)
        :param ServerExecutorClass: Класс Исполнителя полученных команд (для последующей инстанциации)
        """
        super().__init__(server_address, RequestHandlerClass)
        ConfigClass.__init__(self)
        self.open_conn = []
        self.msg_proc = MessageProcessorClass(self)
        self.executor = ServerExecutorClass(self)

    @staticmethod
    def send_message(settings: tuple, message: OutputMessage):
        """
        Статический метод.
        Метод отправки сообщения клиенту.
        Напрямую не использовать! Использовать только для ответа на входящее сообщение.

        :param settings: кортеж (IP: string, PORT: int)
        :param message: сообщение - объект класса OutputMessage
        """
        for msg in message.encode():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((settings[0], settings[1]))
                sock.sendall(bytes(msg, 'utf-8'))
                print("sent {}".format(msg))
                sock.close()


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

    def __init__(self, server_instance: Server):
        """
        Метод инициализации объекта.
        :param server_instance: объект класса Server для работы которого инстанциируется Процессор полученных соединений
        """
        self.server = server_instance

    def get_hashed_sessions(self):
        """
        Метод получения 10 первых символов хэшей активных сеансов.

        :return: словарь формата {хэшсумма сеанса 1: сеанс 1, хэшсумма сеанса 2: сеанс 2, ...}
        """
        return {get_hash(session, self.server.version)[:10]: session for session in self.server.session_list}

    def _preprocess(self, connection: ConnectionClass, new: bool = False):
        """
        Частный метод.
        Берет соединение, которое необходимо от-Процессить и подготавливает его:
        - создаёт объект класса InputMessage основанный на соединении
        - создаёт объект класса OutputMessage если на данное соединение необходимо заранее подготовить ответ

        :param connection: объект класса ConnectionClass - соединение на основании которого будет создано сообщение
        :param new: boolean — True если это новое соединение в текущем сеансе работы сервера и для него будет отдельно
        создано ответное сообщение
        :return:
        message - подготовленный экземпляр класса InputMessage для дальшейшего Процессинга (сообщение),
        callback (опционально) - подготовленный экземпляр класса OutputMessage (ответное сообщение)
        """
        input_params = []
        for key_value in connection.data:
            input_params.append(parse_string(key_value))
        message = InputMessage(self.server.chunk_size, input_params)
        if new:
            return message
        else:
            callback = OutputMessage((self.get_hashed_sessions()[connection.hash_trace],
                                      self.server.version,
                                      self.server.chunk_size))
        return message, callback

    @staticmethod
    def _set_callback_attr(callback: OutputMessage, cmd_value: str, msg_value: str):
        """
        Статический частный метод.
        Присваивает некоторым аттрибутам экземпляра callback переданные в метод значения.

        :param callback: экземпляр класса OutputMessage, аттрибуты которого необходимо обновить
        :param cmd_value: строка - значение для аттрибута cmd
        :param msg_value: строка - значение для аттрибута msg
        """
        setattr(callback, 'cmd', cmd_value)
        setattr(callback, 'msg', msg_value)

    def process_message(self, connection: ConnectionClass):
        """
        Метод Процессинга соединений.
        Проверяет хэш сеанса соединения на присутствие в списке активных сеансов.
        Если присутствует - тогда запускает передает сообщение Исполнителю и возвращает ответное сообщение
        Если хэш сеанса соединения отсутствует в списке активных сеансов - тогда исполняет сообщение
        (ожидается что в сообщении будет команда initialize_session - а значит сеанс будет инициализирован на сервере),
        далее возвращает ответное сообщение.

        :param connection: экземпляр класса connection — установленное соединение, которое необходимо от-Процессить.
        :return: экземпляр класса OutputMessage — сообщение-ответ на входящее сообщение.
        """

        if connection.hash_trace in self.get_hashed_sessions().keys():
            message, callback = self._preprocess(connection)
            try:
                self.execute_message(message)
                self._set_callback_attr(callback, 'svr_approve', getattr(message, 'cmd'))
                setattr(callback, 'id', getattr(message, 'id'))
            except Exception as e:
                setattr(callback, 'cmd', 'svr_error')
                setattr(callback, 'msg', e)
                setattr(callback, 'id', getattr(message, 'id'))
            finally:
                del connection
                return callback
        elif connection.hash_trace == get_hash(0, self.server.version)[:10]:
            message = self._preprocess(connection, True)
            try:
                identifier = self.execute_message(message)
                callback = OutputMessage((identifier,
                                          self.server.version,
                                          self.server.chunk_size))
                self._set_callback_attr(callback, 'approve_init', identifier)
                setattr(callback, 'id', getattr(message, 'id'))
            except Exception as e:
                print(e)
                callback = None
            del connection
            return callback
        else:
            print('Not Existing session')
            del connection
            return 0

    def execute_message(self, message: InputMessage):
        """
        Метод проверки и исполнения команды из входящего сообщения.
        Устанавливает соответствие между командой входящего сообщения
        и методом экземпляра Исполнителя полученных команд.

        :param message: экземпляр класса InputMessage — сообщение, которое содержит исполняемую команду
        """
        cmd = getattr(message, 'cmd')
        if cmd in getattr(self.server.executor, '_get_available_commands')():
            try:
                result = getattr(self.server.executor, cmd)(message)
                return result
            except Exception as e:
                raise e
        else:
            print('Server command {} not available'.format(cmd))


class ServerExecutor(object):
    """
    ServerExecutor - класс Исполнителей полученных команд.
    Исполняет команды, полученные от других приложений.
    Доступные команды представляют собой публичные методы этого класса.

    Новая команда должна добавляться объявлением соответствующего метода, для которого единственным аргументом будет
    экземпляр класса InputMessage!
    """
    def __init__(self, server_instance: Server):
        """
        Метод инициализации объекта.

        :param server_instance: объект класса Server для работы которого инстанциируется Исполнитель полученных команд.
        """
        self.server = server_instance

    @staticmethod
    def svr_print(message: InputMessage):
        """
        Статический метод.
        Выводит текст msg из экземпляра класса InputMessage в стандартный поток ввода-вывода.

        :param message: экземпляр класса InputMessage
        :return:
        """
        print(message.msg)

    def initialize_session(self, message: InputMessage) -> int:
        """
        Метод инициализации сеанса на сервере.
        Добавляет сеанс в список активных сеансов сервера.

        :param message: экземпляр класса InputMessage
        :return: int возвращает идентификатор, присвоенный данному сеансу - чтобы клиент смог себе его присвоить.
        """
        identifier = len(self.server.session_list) + 1
        self.server.session_list.update({identifier: [message.msg.split(':')[0],
                                                      message.msg.split(':')[1]]})
        return identifier

    def delete_session(self, message: InputMessage):
        """
        Метод завершения сеанса клиента на сервере.
        Удаляет сеанс из списка активных сеансов сервера.

        :param message: экземпляр класса InputMessage
        """
        # del self.server.session_list[]

    def svr_greeting(self, message: InputMessage):
        """
        Метод приветствия.

        :param message: экземпляр класса InputMessage
        """
        print('Hello from {}:{}!'.format(self.server.server_address[0], self.server.server_address[1]))

    def _get_available_commands(self) -> list:
        """
        Частный метод.
        Метод получения доступных публичных методов из собственного класса.

        :return: list из существубличных методов
        """
        return [key for key in [s for s in dir(self) if s[:1] != '_' and callable((getattr(self, s)))]]




    @staticmethod
    def ping_pong(message: InputMessage) -> str:
        """
        Статический метод.
        Пинг понг — возвращает клиенту msg из сообщения, полученного с клиента.
        :param message: экземпляр класса InputMessage
        :return: str — текст аттрибута msg объекта message
        """
        return message.msg


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """
    ThreadedTCPRequestHandler - класс Обработчиков входящих запросов.
    При получении TCP запроса - обрабатывает, создаёт соединение (экземпляр класса ConnectionClass) и обновляет его
    пока не получит все части сообщения от клиента.

    data — информация получаемая от клиента (последовательность байт).
    Для понимания почему происходит такая на первый взгляд странная декодировка,
    лучше обратиться в справку класса OutputMessage.
    """

    def handle(self):
        """
        Метод handle вызывается как только сервер получает запрос от клиента.
        """
        data = str(self.request.recv(self.server.chunk_size), 'utf-8')
        print("got {} from {}".format(data, self.client_address))
        session_hash = data.split(':')[0]

        if len(session_hash) == 40:
            size_list = [True if int(i) > self.server.chunk_size else False for i in
                         data.split(':')[1][:-1].split('|')[:-1]]
            size_list.insert(0, False)
            connection = ConnectionClass(session_hash, size_list)
            self.server.open_conn.append(connection)

        elif len(session_hash) == 10:
            for connection in self.server.open_conn:
                if session_hash == connection.hash_trace:
                    if not connection.size_list[len(connection.data)]:
                        connection.data.append(data.split(':', 1)[1])
                    else:
                        connection.data[-1] += data.split(':', 1)[1]

                else:
                    print('InvalidConnection! Failed to update {}'.format(session_hash))

        elif len(session_hash) == 20:
            for connection in self.server.open_conn:
                if session_hash[:10] == connection.hash_trace:
                    self.server.open_conn.remove(connection)
                    response = self.server.msg_proc.process_message(connection)
                    self.server.send_message(('localhost', 15152), response)
                else:
                    print('InvalidConnection! Failed to remove {}'.format(session_hash))

