
from mongoengine import *

class Streets(Document):
    name=StringField(max_length=50)
    longtitude=FloatField()
    latitude=FloatField()
    meta={
        'db_alias':'coord',
        'collection':'Streets'
    }
