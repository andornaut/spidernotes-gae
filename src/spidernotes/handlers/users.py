from __future__ import unicode_literals
import logging

from google.appengine.ext import ndb

from spidernotes.handlers import BaseHandler
from spidernotes.handlers.authentication import AUTH_SESSION_KEY
from spidernotes.models import Note
from spidernotes.users import (
    connect_user, create_auth_id, create_user, disconnect_user,
    get_unauthenticated_auth_id, is_connected)


_log = logging.getLogger(__name__)


class _BaseUserHandler(BaseHandler):
    """Base class for user-related request handlers."""

    def render_user_json(self, user):
        """
        Return a json representation of the current
        :class:`google.appengine.api.users.User`.

        :param user: Current user.
        :type user: :class:`webapp2_extras.appengine.auth.models.User`
        """
        auth_id = get_unauthenticated_auth_id(user)
        if not auth_id:
            _log.error('auth_id not found for user: {}'.format(user))
            self.raise_error()

        return self.render_json({'email': getattr(user, 'email', None),
                                 'name': getattr(user, 'name', None),
                                 'provider': getattr(user, 'provider', None),
                                 'isConnected': is_connected(user),
                                 'token': auth_id})


class UserHandler(_BaseUserHandler):
    """
    Manages :class:`google.appengine.api.users.User` instances.
    """

    @ndb.toplevel
    def get(self):
        """
        Return a :class:`google.appengine.api.users.User` - either the
        current user or a newly created one. If the session contains
        Social Login account information, then connect the user with that Social
        Login account.
        """
        user = self.get_user() or create_user(self.auth.store.user_model)
        try:
            key = self.session.pop(AUTH_SESSION_KEY)
        except KeyError:
            pass
        else:
            user = connect_user(user, key)
            user.put()
        return self.render_user_json(user)

    @ndb.toplevel
    def delete(self):
        """
        Delete the current :class:`google.appengine.api.users.User`.
        """
        user = self.get_user()
        if user:
            if is_connected(user):
                disconnect_user(user)

            user_key = user.key
            Note.delete_all(user_key)
            user_key.delete()
        return self.render_json('')


class DisconnectHandler(_BaseUserHandler):
    def post(self):
        """
        Delete any associations between the current
        :class:`google.appengine.api.users.User` and its Social Login
        identities.
        """
        user = self.get_valid_user()
        if is_connected(user):
            disconnect_user(user)
            user.add_auth_id(create_auth_id())
            user.put()
        else:
            _log.warn('Invalid disconnect request for user: {}'.format(user))
        return self.render_user_json(user)