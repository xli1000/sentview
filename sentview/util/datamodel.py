from ..shared import Base

class DictMixin(object):
	def __init__(self, **kwargs):
		for key in self.__mapper__.c.keys():
			if key in kwargs:
				setattr(self, key, kwargs.get(key))
