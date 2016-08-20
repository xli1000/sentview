import os
import string

class base_config(object):
	DB_USERNAME = os.environ['DB_USERNAME']
	DB_PASSWORD = os.environ['DB_PASSWORD']
	DB_HOST = os.environ['DB_HOST']
	DB_PORT = os.environ.get('DB_PORT', 5432)
	DB_DB = os.environ['DB_DB']
	TWITTER_ACCESS_TOKEN_KEY = os.environ['TWITTER_ACCESS_TOKEN_KEY']
	TWITTER_ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
	TWITTER_CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
	TWITTER_CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
	
	DB_URI = string.Template('postgresql://$username:$password@$host:$port/$db').substitute(
		username = DB_USERNAME,
		password = DB_PASSWORD,
		host = DB_HOST,
		port = DB_PORT,
		db = DB_DB
	)
	

config = base_config
