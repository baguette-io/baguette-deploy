#-*- coding:utf-8 -*-
import datetime
from farine.connectors.sql import *#pylint:disable=wildcard-import,unused-wildcard-import

class Deployment(Model):
    """
    Deployment table representation:
     - uid
     - owner
     - namespace
     - name
     - date_created
    """
    uid = UUIDField(primary_key=True)
    owner = CharField()
    namespace = CharField()
    name = CharField()
    date_created = DateTimeField(default=datetime.datetime.now)

class Status(Model):
    """
    Status table representation:
     - status : deploying, unhealthy, running, terminating, terminated, aborted
     - date_created
    """
    uid = ForeignKeyField(Deployment)
    status = CharField()
    date_created = DateTimeField(default=datetime.datetime.now)
