import socket
import socketserver

from server.message import InputMessage, OutputMessage
from server.utils import get_hash, parse_string


class MessageProcessor(object):

    def __init__(self, server_instance):
        self.server = server_instance

    def get_hashed_sessions(self):
        return {get_hash(session, self.server.version)[:10]: session for session in self.server.session_list}

    def _preprocess(self, connection, new=None):
        input_params = []
        for key_value in connection[1]:
            input_params.append(parse_string(key_value))
        message = InputMessage(self.server.chunk_size, input_params)
        if new:
            callback = OutputMessage((new,
                                      self.server.version,
                                      self.server.chunk_size))
        else:
            callback = OutputMessage((self.get_hashed_sessions()[connection[0][0]],
                                      self.server.version,
                                      self.server.chunk_size))
        return message, callback

    @staticmethod
    def _set_callback_attr(callback, cmd_value, msg_value):
        setattr(callback, 'cmd', cmd_value)
        setattr(callback, 'msg', msg_value)

    def process_message(self, connection):
        if connection[0][0] == get_hash(0, self.server.version)[:10]:
            self.server.session_list.append(1523)
            message, callback = self._preprocess(connection, 1523)

            self._set_callback_attr(callback, 'approve_init', 1523)
            setattr(callback, 'id', getattr(message, 'id'))
            return callback
        elif connection[0][0] in self.get_hashed_sessions().keys():
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
                return callback
        else:
            print('Not Existing session')
            return 0

    def execute_message(self, message):
        cmd = getattr(message, 'cmd')
        if cmd in getattr(self.server.executor, '_get_available_commands')():
            try:
                getattr(self.server.executor, cmd)(message)
            except Exception as e:
                raise e
        else:
            print('Server command {} not available'.format(cmd))


class ConfigClass(object):
    def __init__(self):
        self.version = '0.1'
        self.session_list = []
        self.small_cache_size = 10
        self.chunk_size = 1024
        self.command_list = ['svr_print', 'svr_greeting']


class ServerExecutor(object):
    def __init__(self, server_instance):
        self.server = server_instance

    @staticmethod
    def svr_print(message):
        print(message.msg)

    def initialize_session(self, message):
        self.server.session_list.append(message.msg)

    def svr_greeting(self, message):
        print('Hello from {}:{}!'.format(self.server.server_address[0], self.server.server_address[1]))

    def _get_available_commands(self):
        return [key for key in [s for s in dir(self) if s[:1] != '_' and callable((getattr(self, s)))]]


class Server(socketserver.ThreadingTCPServer, ConfigClass):
    def __init__(self, server_address, RequestHandlerClass, MessageProcessorClass, ServerExecutorClass):
        super().__init__(server_address, RequestHandlerClass)
        ConfigClass.__init__(self)
        self.open_conn = []
        self.msg_proc = MessageProcessorClass(self)
        self.executor = ServerExecutorClass(self)

    @staticmethod
    def send_message(settings, message):
        for msg in message.encode():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((settings[0], settings[1]))
                sock.sendall(bytes(msg, 'utf-8'))
                sock.close()


class ServerThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(self.server.chunk_size), 'utf-8')
        print(data)
        session_hash = data.split(':')[0]

        if len(session_hash) == 40:
            size_list = [True if int(i) > self.server.chunk_size else False for i in
                         data.split(':')[1][:-1].split('|')[:-1]]
            size_list.insert(0, False)
            self.server.open_conn.append([[session_hash[:10], size_list], []])

        elif len(session_hash) == 20:
            for _conn in self.server.open_conn:
                if session_hash[:10] == _conn[0][0]:
                    self.server.open_conn.remove(_conn)
                else:
                    print('InvalidConnection! Failed to remove {}'.format(session_hash))
                response = self.server.msg_proc.process_message(_conn)
                self.request.sendall(b'response')
                self.server.send_message('localhost', 15152, response)

        elif len(session_hash) == 10:
            for _conn in self.server.open_conn:
                if session_hash == _conn[0][0]:
                    if not _conn[0][1][len(_conn[1])]:
                        _conn[1].append(data.split(':')[1])
                    else:
                        _conn[1][-1] += data.split(':')[1]

                else:
                    print('InvalidConnection! Failed to update {}'.format(session_hash))
