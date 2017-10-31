#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'yancheng'


class Pa(type):
	"""docstring for Pa"""
	def __new__(cls, *args, **kwargs):
		print(cls, args, kwargs)
		return type.__new__(cls, args, kwargs)

	def __init__(self, *kw):
		print(self, "Pa init", kw)



class Chil(Pa):
	"""docstring for Chil"""
	def __init__(self, *kw):
		super(Chil,self).__init__(kw)
		print(self, "chil init", kw)

class Chil2(Chil):
	"""docstring for Chil2"""
	def __init__(self, *kw):
		Chil.__init__(self, kw);
		print(self, "Chil2 init", kw)
		


Chil2('11','22')

# class Demo(object): 

# 	def __init__(self): 
# 		print(dir(self), '__init__() called...')

# 	def __new__(cls, *args, **kwargs): 
# 		print ('__new__() - {cls}'.format(cls=cls)) 
# 		return object.__new__(cls, *args, **kwargs) 


# if __name__ == '__main__':
# 	de = Demo()
