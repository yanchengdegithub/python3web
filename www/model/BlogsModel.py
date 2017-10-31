#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'yancheng'

import sys
sys.path.append("..")

import time, uuid

from common.orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class Blogs(Model):
    __table__ = 'Blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    category_id = IntegerField()
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    read_total = IntegerField()
    created_at = FloatField(default=time.time)
