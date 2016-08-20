import sys
import os
import arrow
from dateutil import parser
from twitter import Api

sys.path.insert(0, os.path.abspath('..'))

from sentview.shared import dbsession
from sentview.tweet.models import Tweet
from sentview.config import config
import requests

api = Api(
	config.TWITTER_CONSUMER_KEY,
	config.TWITTER_CONSUMER_SECRET,
	config.TWITTER_ACCESS_TOKEN_KEY,
	config.TWITTER_ACCESS_TOKEN_SECRET
)

def process_tweet(raw_tweet):
	if 'text' in raw_tweet:
		tw = Tweet(
			text=raw_tweet['text'],
			lang=raw_tweet.get('lang')
		)
		tw.ts = parser.parse(raw_tweet['created_at'])
		if raw_tweet.get('user'):
			tw.username = raw_tweet['user'].get('screen_name')
			if raw_tweet['user'].get('location'):
				tw.loc = raw_tweet['user']['location'][0:63]
		if raw_tweet.get('geo') and raw_tweet['geo'].get('coordinates'):
			tw.lat = raw_tweet['geo']['coordinates'][0]
			tw.lng = raw_tweet['geo']['coordinates'][1]
		
		dbsession.add(tw)
		dbsession.commit()

def main():
	while True:
		try:
			for raw_tweet in api.GetStreamSample():
				process_tweet(raw_tweet)
		except requests.exceptions.ChunkedEncodingError:
			print 'ch'
			continue



if __name__ == '__main__':
	main()
