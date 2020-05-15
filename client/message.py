"""
Подсистема message - описывает возможные классы для сообщений, а так же их поведениие.

MessageUnit - родительский класс сообщений
OutputMessage - класс исходящих сообщений
InputMessage - класс входящих сообщений
"""
from client.utils import utf8len, get_hash
import uuid


class MessageUnit(object):
    """
    MessageUnit - родительский класс сообщений.
    Описывает структуру аттрибутов и методов, общую для всех сообщений.
    """

    def __init__(self, chunk_size, **kwargs):
        """
        Метод инициализации.

        Присваивает заведомо нулевые значения используемым аттрибутам (инициализирует их).
        Сохраняет значение chunk_size для того, последующей кодировки.
        Присваивает инициализируемому экземпляру любые переданные в kwargs параметры.

        :param chunk_size: максимальный размер окна в TCP-соединении
        :param kwargs: дополнительные параметры и их значения, которые необходимо присвоить экзепляру для дальнейшей
        кодировки и передачи
        """
        self.id = 0
        self._hash = 0
        self._session = None
        self._version = None
        self._chunk_size = chunk_size
        for key, value in kwargs.items():
            exec('self.{} = None'.format(key))
            setattr(self, key, value)

    def encode(self) -> list:
        """
        Проходимся по каждому публичному аттрибуту и кодируем экземпляр MessageUnit в list по следующему правилу:
        Первый элемент списка:  "{40 символов _hash}:{длина элемента 2 в байтах}|...|{длина элемента n-1 в байтах}|"
        Второй элемент списка:  "{10 символов _hash}:{наименование аттрибута 1}={значение аттрибута 1}"
        ...
        n-1 элемент списка:     "{10 символов _hash}:{наименование аттрибута k}={значение аттрибута k}"
        n элемент списка:       "{20 символов _hash}:EOF"

        Если длина какого-то элемента получилась больше чем chunk_size то он делится на несколько элементов
        длина которых не превышает chunk_size.

        :return: list - закодированное сообщение, готовое к TCP-передаче
        """
        messages = []
        intro = '{}:'.format(self._hash)
        outro = '{}:EOF'.format(self._hash[:20])
        for key in [s for s in dir(self) if s[:1] != '_'
                                            and not callable(getattr(self, s))
                                            and not s == 'hash']:
            messages.append('{}:{}={}'.format(self._hash[:10], key, getattr(self, key)))
        for msg in messages:
            if utf8len(msg) > self._chunk_size:
                messages.insert(messages.index(msg), msg[:self._chunk_size])
                messages[messages.index(msg)] = '{}:{}'.format(self._hash[:10], msg[self._chunk_size:])
            intro += '{}|'.format(utf8len(msg))

        messages.insert(0, intro)
        messages.append(outro)
        return messages

    @property
    def hash(self):
        return self._hash


class OutputMessage(MessageUnit):
    """
    OutputMessage - класс исходящих сообщений. Дочерний класс для MessageUnit.
    Отличается наличием предопределённых аттрибутов, которые должны быть у исходящего сообщения.
    """

    def __init__(self, settings: tuple, body: tuple = (None, None),
                 **kwargs):
        """
        Метод инициализации.

        :param settings: кортеж из значений (номер сеанса, номер версии, размер окна TCP)
        :param body: кортеж из значений (значение для аттрибута cmd, значение для аттрибута msg)
        :param kwargs: дополнительные аттрибуты и их значения
        """
        super().__init__(settings[2], **kwargs)
        self.id = str(uuid.uuid4())
        self.cmd = body[0]
        self.msg = body[1]
        self._hash = get_hash(settings[0], settings[1])


class InputMessage(MessageUnit):
    """
    InputMessage - класс входящих сообщений. Дочерний класс для MessageUnit.
    Отличается отсутствием предопределённых аттрибутов, и динамическим формированием принятых аттрибутов.
    """
    def __init__(self, chunk_size: int, input_params: list, **kwargs):
        """
        Метод инициализации.

        :param chunk_size: размер окна TCP
        :param input_params: list из параметров в формате [[параметр 1, значение 1],...,[параметр n, значение n]]
        :param kwargs: дополнительные аттрибуты и их значения
        """
        super().__init__(chunk_size, **kwargs)
        self.msg = None
        for key, value in input_params:
            exec('self.{} = None'.format(key))
            setattr(self, key, value)
