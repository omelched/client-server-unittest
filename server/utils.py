import hashlib


def utf8len(s):
    return len(s.encode('utf-8'))


def parse_string(string):
    return string.split('=')


def get_hash(session, version):
    hash_sum = hashlib.sha1()
    hash_sum.update(bytes(session))
    hash_sum.update(bytes(version, encoding='utf-8'))
    return hash_sum.hexdigest()

