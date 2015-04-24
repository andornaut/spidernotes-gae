from __future__ import unicode_literals
import codecs
import datetime
import random
import string
import time


def create_random_id():
    """
    Create and return a randomly generated 64-character long string.

    :return: A random string.
    :rtype: unicode
    """
    return ''.join([random.choice(string.ascii_letters + string.digits)
                    for _ in xrange(64)])


def from_timestamp(timestamp):
    """
    Convert from a JavaScript timestamp to a Python datetime.

    :param unicode timestamp: Timestamp to convert.
    :return: Datetime.
    :rtype: :class:`datetime.datetime`
    """
    timestamp = float(timestamp) / 1000.0
    return datetime.datetime.utcfromtimestamp(timestamp)


def get_param(ctx, key):
    """
    Return an item from the supplied ``ctx`` using the supplied ``key``.

    If the value is a string then strip it.

    :param dict ctx: Dictionary from which to fetch the returned value.
    :param unicode key: Key into the ctx ``dict``.
    :return: An item in the ``ctx`` or ``None``.
    """
    param = ctx.get(key)
    if hasattr(param, 'strip'):
        param = unicode(param.strip())
    return param


def read_utf8_file(path):
    """
    Read a file and return its contents.

    :param unicode path: File path relative to the source directory.
    :return: File text contents.
    :rtype: unicode
    """
    with codecs.open(path, encoding='UTF8') as file_:
        return file_.read()


def to_timestamp(dt):
    """
    Convert from a Python datetime to a JavaScript timestamp.

    :param datetime.datetime dt: Datetime to convert.
    :return: Timestamp that is suitable for being consumed by JavaScript.
    :rtype: ``float``
    """
    ms = time.mktime(dt.timetuple()) * 1000
    mc = dt.microsecond / 1000.0
    return ms + mc
