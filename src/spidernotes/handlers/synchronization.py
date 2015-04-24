from __future__ import unicode_literals
import json
from collections import namedtuple
from datetime import datetime
from itertools import imap

from google.appengine.ext import ndb

from spidernotes.handlers import BaseHandler
from spidernotes.models import Note
from spidernotes.utils import from_timestamp, get_param, to_timestamp


class SynchronizationHandler(BaseHandler):
    """Synchronizes notes to/from the client and server."""

    @ndb.toplevel
    def post(self):
        """
        Merge notes from the client and return notes to the client for it to
        merge.

        :return: json string that contains a ``list`` of
            :class:`spidernotes.models.Note` instances that have changed
            since the last time the notes were synchronized, as well as a
            timestamp of when this request was processed.
        """
        user_key = self.get_valid_user().key
        try:
            ctx = json.loads(self.request.body)
        except ValueError:
            self.raise_error()

        old_last_synchronized = from_timestamp(ctx.get('lastSynchronized'))
        new_last_synchronized = datetime.utcnow()

        notes_from_client = imap(_to_tuple, ctx.get('notes'))
        notes_from_server = _merge_notes(user_key,
                                         notes_from_client,
                                         old_last_synchronized,
                                         new_last_synchronized)

        return self.render_json(
            {'notes': [o.to_dict() for o in notes_from_server],
             'lastSynchronized': to_timestamp(new_last_synchronized)})


_NoteTuple = namedtuple(
    'NoteTuple', ['id', 'body', 'url', 'is_deleted', 'created', 'modified'])


def _to_tuple(note_dict):
    """
    Return a ``namedtuple`` representation of the supplied ``note_dict``.

    :param dict note_dict: ``dict`` representation of a
        :class:`spidernotes.models.Note`
    """
    is_deleted = bool(note_dict.get('isDeleted'))
    return _NoteTuple(
        id=get_param(note_dict, 'id'),
        body=get_param(note_dict, 'body') if not is_deleted else '',
        url=get_param(note_dict, 'url') if not is_deleted else '',
        is_deleted=is_deleted,
        created=from_timestamp(get_param(note_dict, 'created')),
        modified=from_timestamp(get_param(note_dict, 'modified')))


def _merge_notes(user_key, notes_from_client, old_last_synchronized,
                 new_last_synchronized):
    """
    Merge notes from client with notes from the server.

    :param user_key: Key of the :class:`google.appengine.api.users.User`
        with which the notes are associated.
    :param notes_from_client: Iterable of Note-like objects.
    :param datetime.datetime old_last_synchronized: Datetime after which to
        fetch server notes.
    :param datetime.datetime new_last_synchronized: Datetime of the current
        merge operation.
    :type user_key: :class:`google.appengine.ext.db.Key`
    :return: Notes to be merged back into the client.
    :rtype: list
    """
    from_server_map = {o.key: o for o in Note.get_synchronized_after(
        user_key, old_last_synchronized)}
    to_persist = []

    for client_note in notes_from_client:
        server_note, is_created = Note.get_or_create(user_key,
                                                     client_note.id)
        if is_created or client_note.modified >= server_note.modified:
            server_note.update_from_note(client_note, new_last_synchronized)
            to_persist.append(server_note)

            # The ``client_note`` supersedes the ``server_note``, so don't
            # return the ``server_note`` to the client.
            from_server_map.pop(server_note.key, None)

    if to_persist:
        ndb.put_multi_async(to_persist)
    return from_server_map.values()