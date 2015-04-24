"""
Provides functions for managing users.
"""

from __future__ import unicode_literals
from itertools import imap

from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import Unique

from spidernotes.models import Note
from spidernotes.utils import create_random_id


_UNAUTHENTICATED_PREFIX = 'spidernotes:'


def connect_user(user, data):
    """
    Connect ``user`` to the Social Login account indicated by ``auth_data``.

    If a user that is associated with ``auth_data`` already exists, then copy
    the notes from the supplied ``user`` to the other user and return the other
    user. Otherwise, add the auth data to ``user`` and return ``user``.

    The caller is responsible for persisting the ``user``.

    :param user: The current user.
    :param dict data: Social Login data.
        Required keys: id, provider
        Optional keys: email, name
    :type user: :class:`webapp2_extras.appengine.auth.models.User`
    :return: User that is associated with the Social Login account indicated by
        ``auth_data``..
    :rtype: :class:`webapp2_extras.appengine.auth.models.User`
    """
    provider = data['provider']
    auth_id = '{}:{}'.format(provider, data['id'])
    auth_user = user.get_by_auth_id(auth_id)

    if auth_user:
        old_user = user
        user = auth_user
        _copy_notes_between_users(old_user.key, user.key)
        old_user.key.delete()
    else:
        user.add_auth_id(auth_id)

    user.email = data.get('email')
    user.name = data.get('name')
    user.provider = provider
    return user


def create_auth_id():
    """
    Create and return an unauthenticated auth_id.

    :return: Newly generated auth_id.
    :rtype: ``unicode``
    """
    return '{}{}'.format(_UNAUTHENTICATED_PREFIX, create_random_id())


def create_user(user_class):
    """
    Return a new :class:`webapp2_extras.appengine.auth.models.User` or ``None``
    if there is an error.

    :param class user_class: User class.
    :return: Newly created user.
    :rtype: :class:`webapp2_extras.appengine.auth.models.User` or ``None``
    """
    ok, user = user_class.create_user(auth_id=create_auth_id(),
                                      id=create_random_id())
    return user


def disconnect_user(user):
    """
    Delete all auth_ids that are associated with the supplied ``user``.

    The caller is responsible for connecting a new unauthenticated auth_id and
    for persisting the ``user``.

    :param user: User to disconnect.
    :type user: :class:`webapp2_extras.appengine.auth.models.User`
    """
    for auth_id in user.auth_ids:
        # Delete all auth_id ``Unique`` entities.
        unique = '{}.auth_id:{}'.format(user.__class__.__name__, auth_id)
        ndb.model.Key(Unique, unique).delete()

    user.auth_ids = []
    user.email = None
    user.name = None
    user.provider = None


def get_unauthenticated_auth_id(user):
    """
    Return an auth_id that is not associated with a Social Login provider, or
    ``None`` if such an auth_id does not exist.

    :param user: User from which to retrieve the auth_id.
    :type user: :class:`webapp2_extras.appengine.auth.models.User`
    :rtype: ``unicode`` or ``None``
    """
    for auth_id in user.auth_ids:
        if auth_id.startswith(_UNAUTHENTICATED_PREFIX):
            return auth_id


def is_connected(user):
    """
    Return ``True`` if the user has an associated Social Login identity.

    :param user: User to connect.
    :type user: :class:`webapp2_extras.appengine.auth.models.User`
    :rtype: ``bool``
    """
    is_unauthenticated_id = lambda o: not o.startswith(_UNAUTHENTICATED_PREFIX)
    return any(imap(is_unauthenticated_id, user.auth_ids))


def _copy_notes_between_users(from_user_key, to_user_key):
    """
    Copy notes from one :class:`google.appengine.api.users.User` to
    another.

    :param from_user_key: Key of the :class:`google.appengine.api.users.User`
        from which to copy the notes.
    :param to_user_key: Key of the :class:`google.appengine.api.users.User`
        to which to copy the notes.
    :type from_user_key: :class:`google.appengine.ext.db.Key`
    :type to_user_key: :class:`google.appengine.ext.db.Key`
    """
    notes = [src.copy_to_user(to_user_key)
             for src in Note.get_active(from_user_key)]
    if notes:
        ndb.put_multi_async(notes)