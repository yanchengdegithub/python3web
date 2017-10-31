#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'yancheng'

import sys
sys.path.append("..")

import time, uuid

from common.orm import Model, StringField, BooleanField, FloatField, TextField, close_pool

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class Users(Model):
    __table__ = 'Users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)

    def __del__(self):
    	close_pool()