from server.utils import utf8len, get_hash


class MessageUnit(object):
    def __init__(self, chunk_size, **kwargs):
        self._hash = 0
        self._session = None
        self._version = None
        self._chunk_size = chunk_size
        for key, value in kwargs.items():
            exec('self.{} = None'.format(key))
            setattr(self, key, value)

    def encode(self):
        messages = []
        intro = '{}:'.format(self._hash)
        outro = '{}:EOF'.format(self._hash[:20])
        for key in [s for s in dir(self) if s[:1] != '_' and not callable(getattr(self, s))]:
            messages.append('{}:{}={}'.format(self._hash[:10], key, getattr(self, key)))
        for msg in messages:
            if utf8len(msg) > self._chunk_size:
                messages.insert(messages.index(msg), msg[:self._chunk_size])
                messages[messages.index(msg)] = '{}:{}'.format(self._hash[:10], msg[self._chunk_size:])
            intro += '{}|'.format(utf8len(msg))

        messages.insert(0, intro)
        messages.append(outro)
        return messages


class OutputMessage(MessageUnit):
    def __init__(self, settings, body=(None, None), **kwargs):  # settings = (session, version, chunk_size); body = (
        # cmd, msg)
        super().__init__(settings[2], **kwargs)
        self.cmd = body[0]
        self.msg = body[1]
        self._hash = get_hash(settings[0], settings[1])


class InputMessage(MessageUnit):
    def __init__(self, chunk_size, input_params, **kwargs):
        super().__init__(chunk_size, **kwargs)
        for key, value in input_params:
            exec('self.{} = None'.format(key))
            setattr(self, key, value)
