#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'yancheng'

import sys
sys.path.append("..")

import asyncio
from common import orm

from model import UsersModel, BlogsModel, CommentsModel

@asyncio.coroutine
def createUser(loop):
    
    yield from orm.create_pool(loop=loop,user='root', password='InfogoAsmPass@168', database='python3')

    u = UsersModel.Users(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    yield from u.save()

@asyncio.coroutine
def selectAllUser(loop):
	yield from orm.create_pool(loop=loop,user='root', password='InfogoAsmPass@168', database='python3')
	u = UsersModel.Users()
	print(u.findAll())

loop = asyncio.get_event_loop()
loop.run_until_complete(selectAllUser(loop))
loop.close()
if loop.is_closed():
	sys.exit(0)
