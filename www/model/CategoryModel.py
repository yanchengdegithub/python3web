#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'yancheng'

import sys
sys.path.append("..")

import time, uuid

from common.orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class Category(Model):
    __table__ = 'Category'

    id = IntegerField(primary_key=True)
    name = StringField(ddl='varchar(255)')
    p_id = IntegerField()
    path_id = StringField(ddl='varchar(255)')
    orders = IntegerField()
    user_id = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
