from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from flask_socketio import SocketIO, emit
from sentview.config import config

engine = create_engine(
	config.DB_URI, 
	connect_args={'connect_timeout': 10, 'options': '-c timezone=utc'},
	pool_recycle=300
)
dbsession = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
socketio = SocketIO(message_queue=config.MESSAGE_QUEUE)