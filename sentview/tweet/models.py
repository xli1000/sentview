from sqlalchemy import Column, Integer, String, DateTime, Index, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from ..util.datamodel import DictMixin
from ..shared import Base

class Tweet(Base, DictMixin):
	__tablename__ = 'tweet'
	id = Column(Integer, primary_key=True, autoincrement=True)
	text = Column(Text)
	lang = Column(String(8), index=True)
	username = Column(String(20))
	ts = Column(DateTime, index=True) # create date
	loc = Column(String(63)) # comment string from user
	lat = Column(DOUBLE_PRECISION)
	lng = Column(DOUBLE_PRECISION)
	retweet = Column(Boolean)
	sent_score = Column(Float, index=True) # compound sentiment score between -1 and 1 calculated by VADER
	
	def __init__(self, **kwargs):
		DictMixin.__init__(self, **kwargs)
