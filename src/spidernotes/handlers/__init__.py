from __future__ import unicode_literals
import json
import logging

from google.appengine.ext.db import BadRequestError
from webapp2 import cached_property, RequestHandler
from webapp2_extras import auth, sessions, sessions_memcache
from webapp2_extras.appengine.auth.models import User

from spidernotes.utils import read_utf8_file, get_param


_log = logging.getLogger(__name__)

_AUTH_ID_HEADER_KEY = 'X-Messaging-Token'


class BaseHandler(RequestHandler):
    """
    Base class for all request handlers.
    """

    @cached_property
    def auth(self):
        """Return an instance of :class:`webapp2_extras.auth.Auth`."""
        return auth.get_auth()

    def dispatch(self):
        """Dispatch the request."""
        self.session_store = sessions.get_store(request=self.request)
        try:
            super(BaseHandler, self).dispatch()
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    def get_user(self):
        """
        Return the current :class:`google.appengine.api.users.User` or
        ``None``.
        """
        user = None
        auth_id = get_param(self.request.headers, _AUTH_ID_HEADER_KEY)
        if auth_id:
            try:
                user = User.get_by_auth_id(auth_id)
            except BadRequestError:
                _log.exception('Error getting user by auth_id: {}'.format(
                    auth_id))
        return user

    def get_valid_user(self):
        """
        Return the current :class:`google.appengine.api.users.User`, or if one
        does not exist then raise a "forbidden" error.
        """
        return self.get_user() or self.raise_forbidden()

    def raise_error(self, *args, **kwargs):
        """Raise a general error."""
        self.abort(500, *args, **kwargs)

    def raise_forbidden(self, *args, **kwargs):
        """Raise a forbidden error."""
        self.abort(403, *args, **kwargs)

    def render_json(self, obj):
        """
        Convert the supplied ``obj`` to a json string and write the result to
        the HTTP response.

        :param obj: Object to convert to a json string.
        """
        # Headers must be strings.
        self.response.headers.add_header(str('Content-Type'),
                                         str('application/json'))
        response = json.dumps(obj, ensure_ascii=False)

        # ``json.dumps()`` may or may not return ``unicode`` (see the
        # documentation of the ``ensure_ascii`` parameter).
        response = unicode(response)
        self.response.out.write(response)

    @cached_property
    def session(self):
        """Return a session object."""
        factory = sessions_memcache.MemcacheSessionFactory
        return self.session_store.get_session(factory=factory)


class DefaultHandler(BaseHandler):
    def get(self):
        """Display a simple default page."""
        self.response.write(read_utf8_file('templates/home.html'))


def handle_404(request, response, exception):
    """Display a 404 error page."""
    _handle_http_error(response, exception, 404, 'Resource not found.')


def handle_500(request, response, exception):
    """Display a 500 error page."""
    _handle_http_error(response, exception, 500, 'A server error occurred!')


def _handle_http_error(response, exception, response_code, message):
    _log.error(exception)
    response.set_status(response_code)
    response.write(message)