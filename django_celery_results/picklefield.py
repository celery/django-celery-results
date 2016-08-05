"""
    Based on django-picklefield which is
    Copyright (c) 2009-2010 Gintautas Miliauskas
    but some improvements including not deepcopying values.

    Provides an implementation of a pickled object field.
    Such fields can contain any picklable objects.

    The implementation is taken and adopted from Django snippet #1694
    <http://www.djangosnippets.org/snippets/1694/> by Taavi Taijala,
    which is in turn based on Django snippet #513
    <http://www.djangosnippets.org/snippets/513/> by Oliver Beattie.
"""
from __future__ import absolute_import, unicode_literals

from base64 import b64encode, b64decode

from celery.utils.serialization import pickle
from kombu.utils.encoding import bytes_to_str

from django.db import models
from django.utils.encoding import force_text


DEFAULT_PROTOCOL = 2

NO_DECOMPRESS_HEADER = b'\x1e\x00r8d9qwwerwhA@'


class PickledObject(str):
    pass


class PickledObjectField(models.Field):

    def __init__(self, protocol=DEFAULT_PROTOCOL,
                 *args, **kwargs):
        self.protocol = protocol
        kwargs.setdefault('editable', False)
        super(PickledObjectField, self).__init__(*args, **kwargs)

    def get_default(self):
        if self.has_default():
            return self.default() if callable(self.default) else self.default
        return super(PickledObjectField, self).get_default()

    def dumps(self, value, pickle_protocol=DEFAULT_PROTOCOL):
        return bytes_to_str(b64encode(pickle.dumps(value, self.protocol)))

    def loads(self, value):
        return pickle.loads(b64decode(value))

    def to_python(self, value):
        if value is not None:
            try:
                return self.loads(value)
            except Exception:
                if isinstance(value, PickledObject):
                    raise
                return value

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def get_db_prep_value(self, value, **kwargs):
        if value is not None and not isinstance(value, PickledObject):
            return force_text(self.dumps(value))
        return value

    def value_to_string(self, obj):
        return self.get_db_prep_value(self._get_val_from_obj(obj))

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value, *args, **kwargs):
        if lookup_type not in ['exact', 'in', 'isnull']:
            raise TypeError(
                'Lookup type {0} is not supported.'.format(lookup_type))
        return super(PickledObjectField, self) \
            .get_db_prep_lookup(*args, **kwargs)
