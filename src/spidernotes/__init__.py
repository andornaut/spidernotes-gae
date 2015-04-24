from __future__ import unicode_literals

from webapp2 import Route, WSGIApplication

from secrets import SESSION_KEY
from spidernotes.handlers import DefaultHandler, handle_404, handle_500
from spidernotes.handlers.authentication import AuthHandler
from spidernotes.handlers.synchronization import SynchronizationHandler
from spidernotes.handlers.users import DisconnectHandler, UserHandler


routes = [
    ('/api/disconnect', DisconnectHandler),
    ('/api/sync', SynchronizationHandler),
    ('/api/user', UserHandler),
    Route(
        '/auth/<provider>',
        handler='spidernotes.handlers.authentication.AuthHandler:_simple_auth',
        name='auth_login'),
    Route(
        '/auth/<provider>/callback',
        handler='spidernotes.handlers.authentication.AuthHandler:_auth_callback',
        name='auth_callback'),
    Route(
        '/logout',
        handler='spidernotes.handlers.authentication.AuthHandler:logout',
        name='logout'),
    (r'/.*', DefaultHandler)
]

config = {
    'webapp2_extras.auth': {
        'session_backend': 'memcache',
    },
    'webapp2_extras.sessions': {
        'cookie_name': '_simpleauth_sess',
        'secret_key': str(SESSION_KEY)
    }
}

app = WSGIApplication(routes=routes, config=config)
app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500