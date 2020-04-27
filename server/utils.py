"""
подсистема utils - общая

содержит публичные функции, используемые в большинстве других подсистем, не требующие
объектного контекста

"""

import hashlib


def utf8len(s: str):
    """
    utf8len(s) - возвращает длину строки в UTF-8

    :param s: строка, длину которой в кодировке UTF-8 необходимо узнать
    :return: длина строки
    """
    return len(s.encode('utf-8'))


def parse_string(string: str):
    """
    parse_string(string) - возвращает список из строк, разделённых символом '='

    :param string: строка, которую необходимо разделить
    :return: список из строк
    """
    return string.split('=')


def get_hash(session: int, version: str):
    """
    get_hash(session, version) - возвращает хэшсумму (SHA1) текущих сеанса и версии приложения

    :param session: текущий сеанс приложения
    :param version: текущая версия приложения
    :return: хэшсумма (SHA1)
    """
    hash_sum = hashlib.sha1()
    hash_sum.update(bytes(session))
    hash_sum.update(bytes(version, encoding='utf-8'))
    return hash_sum.hexdigest()
