from sqlalchemy import Column, Integer, String, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from ..util.datamodel import DictMixin
from ..shared import Base

class Tweet(Base, DictMixin):
	__tablename__ = 'tweet'
	id = Column(Integer, primary_key=True, autoincrement=True)
	text = Column(Text)
	lang = Column(String(8))
	username = Column(String(20))
	ts = Column(DateTime, index=True)
	loc = Column(String(63))
	lat = Column(DOUBLE_PRECISION)
	lng = Column(DOUBLE_PRECISION)
	
	def __init__(self, **kwargs):
		DictMixin.__init__(self, **kwargs)
