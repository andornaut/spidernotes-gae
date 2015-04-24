from __future__ import unicode_literals

from google.appengine.ext import ndb
from google.appengine.ext.ndb.key import Key

from spidernotes.utils import to_timestamp


class Note(ndb.Model):
    body = ndb.TextProperty()
    url = ndb.StringProperty()
    is_deleted = ndb.BooleanProperty(required=True, default=False)
    created = ndb.DateTimeProperty(required=True, indexed=False)
    modified = ndb.DateTimeProperty(required=True)
    synchronized = ndb.DateTimeProperty(required=True)

    @classmethod
    def delete_all(cls, user_key):
        """
        Delete all of the notes that are associated with ``user_key``.

        :param user_key:  Key of the :class:`google.appengine.api.users.User`
            for which to delete the notes.
        :type user_key: :class:`google.appengine.ext.db.Key`
        """
        keys = cls._get(user_key).iter(keys_only=True)
        ndb.delete_multi_async(keys)

    @classmethod
    def get_active(cls, user_key):
        """
        Return a :class:`google.appengine.ext.ndb.query.Query` of
        :class:`spidernotes.models.Note` instances that are associated with the
        supplied ``user_key``, and are not marked as deleted..

        :param user_key: Key of the :class:`google.appengine.api.users.User`
            with which the notes are associated.
        :type user_key: :class:`google.appengine.ext.db.Key`
        :return: Query of note keys.
        :rtype: `:class:`google.appengine.ext.ndb.query.Query`
        """
        return cls._get(user_key).filter(cls.is_deleted == False)

    @classmethod
    def get_or_create(cls, user_key, note_id):
        """
        Attempt to fetch and return a :class:`spidernotes.models.Note` that
        is associated with the supplied ``user_key`` and which has the supplied
        ``note_id``, or if it does not exist, then create and return a new note
        with the same. Also, return ``True`` if a new note was created or
        ``False`` otherwise.

        :param user_key: Key of the :class:`google.appengine.api.users.User`
            that is associated with the note.
        :param unicode note_id: Unique note identifier.
        :type user_key: :class:`google.appengine.ext.db.Key`
        :return: Tuple of a Note and a created boolean.
        :rtype: ``tuple``
        """
        note = Key(cls, note_id, parent=user_key).get()
        if note:
            is_created = False
        else:
            note = cls(parent=user_key, id=note_id)
            is_created = True
        return note, is_created

    @classmethod
    def get_synchronized_after(cls, user_key, last_synchronized):
        """
        Return a :class:`google.appengine.ext.ndb.query.Query` of
        :class:`spidernotes.models.Note` instances that are associated with the
        supplied ``user_key``, and were synchronized after the
        ``last_synchronized`` datetime.

        :param user_key: Key of the :class:`google.appengine.api.users.User`
            with which the notes are associated.
        :param datetime.datetime last_synchronized: Datetime after which to
            filter the notes.
        :type user_key: :class:`google.appengine.ext.db.Key`
        :type last_synchronized: :class:`datetime.datetime` or ``None``.
        :return: Query of note keys.
        :rtype: `:class:`google.appengine.ext.ndb.query.Query`
        """
        return cls._get(user_key).filter(cls.synchronized > last_synchronized)

    @classmethod
    def _get(cls, user_key):
        """
        Return a :class:`google.appengine.ext.ndb.query.Query` of
        :class:`spidernotes.models.Note` instances that are associated with the
        supplied ``user_key``.

        :param user_key: Key of the :class:`google.appengine.api.users.User`
            with which the notes are associated.
        :type user_key: :class:`google.appengine.ext.db.Key`
        :return: Query of note keys.
        :rtype: :class:`google.appengine.ext.ndb.query.Query`
        """
        return cls.query(ancestor=user_key).order(-cls.synchronized)

    def copy_to_user(self, to_user_key):
        """
        Return a new Note that is associated with the supplied ``to_user_key``,
        and whose data is copied from this instance.

        :param to_user_key: Key of the :class:`google.appengine.api.users.User`
            with which to associate the new note.
        :type to_user_key: :class:`google.appengine.ext.db.Key`
        :return: Newly created note.
        :rtype: :class:`spidernotes.models.Note`
        """
        from_id = self.key.id()
        return Note(id=from_id,
                    parent=to_user_key,
                    body=self.body,
                    url=self.url,
                    created=self.created,
                    modified=self.modified,
                    synchronized=self.synchronized)

    def to_dict(self):
        """Return a ``dict`` representation of this instance."""
        is_deleted = self.is_deleted
        return {'id': self.key.id(),
                'body': self.body if not is_deleted else '',
                'url': self.url if not is_deleted else '',
                'isDeleted': is_deleted,
                'created': to_timestamp(self.created),
                'modified': to_timestamp(self.modified)}

    def update_from_note(self, from_note, last_synchronized):
        """
        Update this instance with data copied from ``from_note``, and set this
        instance's ``last_synchronized`` datetime.

        :param from_note: Note to copy data from.
        :param datetime.datetime last_synchronized: Datetime to set on this
            instance.
        :type from_note: ``NoteTuple``
        """
        self.body = from_note.body
        self.url = from_note.url
        self.is_deleted = from_note.is_deleted
        self.created = from_note.created
        self.modified = from_note.modified
        self.synchronized = last_synchronized