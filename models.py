
from mongoengine import *

class Houses(Document):
    street=StringField(max_length=50)
    number=IntField()
    longtitude=FloatField()
    latitude=FloatField()
    meta={
        'db_alias':'coord',
        'collection':'Houses'
    }

class Streets(Document):
    name=StringField(max_length=50)
    longtitude=FloatField()
    latitude=FloatField()
    meta={
        'db_alias':'coord',
        'collection':'Streets'
    }
