from __future__ import unicode_literals

from simpleauth import SimpleAuthHandler

from spidernotes import secrets
from spidernotes.handlers import BaseHandler


AUTH_SESSION_KEY = 'auth_data'


class AuthHandler(BaseHandler, SimpleAuthHandler):
    """
    Processes Social Login requests using `simpleauth`_.

    .. _simpleauth: http://code.google.com/p/gae-simpleauth/
    """

    OAUTH2_CSRF_STATE = True  # Enable CSRF cache token for OAuth 2.0

    ATTRS_MAP = {
        'facebook': {
            'email': 'email',
            'name': 'name'
        },
        'google': {
            'email': 'email',
            'name': 'name'
        },
        'twitter': {
            'screen_name': 'email',
        },
        'windows_live': {
            'emails': lambda ctx: {'email': ctx.get('account')},
            'name': 'name'
        },
        'openid': {
            'email': 'email'
        }  # Yahoo!
    }

    def logout(self):
        """Delete the current session."""
        self.auth.unset_session()

    def _callback_uri_for(self, provider):
        """
        Return a callback URL for the second step of the authentication process.

        :param str provider: Name of the Social Login provider.
        """
        return self.uri_for('auth_callback', provider=provider, _full=True)

    def _get_consumer_info_for(self, provider):
        """
        Return a tuple of (key, secret, desired_scopes).

        :param str provider: Name of an Social Login provider.
        """
        return secrets.AUTH_CONFIG[provider]

    def _on_signin(self, data, _, provider):
        """
        Save the Social Login authentication information to the session.

        :param dict data: User-info dictionary.
        :param _: Access token and secret. Unused.
        :param str provider: Name of the Social Login provider.
        """
        provider = unicode(provider)
        converted_data = {
            'id': data['id'],
            'provider': 'yahoo' if provider == 'openid' else provider
        }

        for k, v in self.ATTRS_MAP[provider].items():
            k = data.get(k)
            converted_data.update(v(k) if callable(v) else {v: k})

        self.session[AUTH_SESSION_KEY] = converted_data