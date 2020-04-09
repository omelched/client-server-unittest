import hashlib


def parse_string(string):
    return string.split('=')


def utf8len(s):
    return len(s.encode('utf-8'))


def get_hash(session, version):
    hash_sum = hashlib.sha1()
    hash_sum.update(bytes(int(session)))
    hash_sum.update(bytes(version, encoding='utf-8'))
    return hash_sum.hexdigest()