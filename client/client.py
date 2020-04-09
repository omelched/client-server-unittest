import socket
import socketserver

from client.message import InputMessage
from client.utils import parse_string, get_hash


class ConfigClass(object):
    def __init__(self):
        self.version = '0.1'
        self.small_cache_size = 10
        self.chunk_size = 1024


class MessageProcessor(object):

    def __init__(self, client_instance):
        self.client = client_instance

    def process_response(self, connection):

        input_params = []
        for key_value in connection[1]:
            input_params.append(parse_string(key_value))
        message = InputMessage(self.client.chunk_size, input_params)
        self.execute_message(message)

    def execute_message(self, message):
        cmd = getattr(message, 'cmd')
        if cmd in getattr(self.client.executor, '_get_available_commands')():
            try:
                getattr(self.client.executor, cmd)(message)
            except Exception as e:
                raise e
        else:
            print('Client command {} not available'.format(cmd))


class ClientExecutor(object):
    def __init__(self, client_instance):
        self.client = client_instance

    @staticmethod
    def clt_print(message):
        print(message.msg)

    def approve_init(self, message):
        self.client.app.session = message.msg


    @staticmethod
    def svr_approve(message):
        print('Server successfully executed command {}!'.format(message.msg))

    def _get_available_commands(self):
        return [key for key in [s for s in dir(self) if s[:1] != '_' and callable((getattr(self, s)))]]


class Client(socketserver.ThreadingTCPServer, ConfigClass):
    def __init__(self, app, client_address, RequestHandlerClass, MessageProcessorClass, ClientExecutorClass):
        self.app = app
        super().__init__(client_address, RequestHandlerClass)
        ConfigClass.__init__(self)
        self.msg_proc = MessageProcessorClass(self)
        self.executor = ClientExecutorClass(self)
        self.connection_buffer = []
        self.pending_messages = []

    def send_message(self, settings, message):
        for msg in message.encode():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((settings[0], settings[1]))
                sock.sendall(bytes(msg, 'utf-8'))
                print("sent {}".format(msg))
                sock.close()
        self.pending_messages.append(message.id)


class ClientThreadedTCPRequestHandler(socketserver.BaseRequestHandler):  # заточить на работу с одним сервером

    def handle(self):
        data = str(self.request.recv(self.server.chunk_size), 'utf-8')
        print("got {}".format(data))
        session_hash = data.split(':')[0]

        if len(session_hash) == 40:
            size_list = [True if int(i) > self.server.chunk_size else False for i in
                         data.split(':')[1][:-1].split('|')[:-1]]
            size_list.insert(0, False)
            self.server.connection_buffer = [[session_hash[:10], size_list], []]

        elif len(session_hash) == 20:
            self.server.msg_proc.process_response(self.server.connection_buffer)

        elif len(session_hash) == 10:

            if not self.server.connection_buffer[0][1][len(self.server.connection_buffer[1])]:
                self.server.connection_buffer[1].append(data.split(':')[1])
            else:
                self.server.connection_buffer[1][-1] += data.split(':')[1]