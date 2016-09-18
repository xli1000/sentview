import logging
import os
import sys
import time

import arrow
from flask_socketio import SocketIO, emit
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from ratelimit import rate_limited
import sqlalchemy.exc
from sqlalchemy.sql import text
import time

sys.path.insert(0, os.path.abspath('..'))

import queries
from sentview.config import config
from sentview.shared import dbsession, engine
from sentview.tweet.models import Tweet
from sentview.util.errors import InvalidStateError
from sentview.util.intervals import INTERVAL_1S, INTERVAL_15MIN, INTERVALS

MAX_BATCH_SIZE = 400
DB_CONNECTION_ERROR_WAIT_TIME = 1 # second

logger = logging.getLogger(__name__)

class TweetProcessor(object):
	def __init__(self, db_engine, sent_analyzer=None, socket=None):
		"""
		Args:
			db_engine: SQLAlchemy engine
			sent_analyzer: Sentiment Intensity Analyzer
		"""
		self.engine = db_engine
		if sent_analyzer is None:
			self.sent_analyzer = SentimentIntensityAnalyzer()
		else:
			self.sent_analyzer = sent_analyzer
		self.socket = socket

	def get_last_processed_id(self):
		"""
		Returns:
			the ID of the last Tweet that has already been processed.
		"""
		results = [
			row for row in 
			self.engine.execute(queries.SELECT_LAST_PROCESSED_ID) 
		]
		if len(results) == 0:
			raise InvalidStateError('Last processed Tweet ID was not set in the database.')

		return results[0][0]

	def score_tweets(self, start_id):
		"""
		Updates each Tweet with a calculated sentiment score. 

		Args:
			start_id: will score all Tweets with IDs >= to this value.
		Returns: 
			the ID of the last tweet that was assigned a score.
		"""
		with self.engine.connect() as connection:
			tweets = connection.execute(queries.SELECT_TWEETS, start_id, MAX_BATCH_SIZE)
			
			trans = connection.begin()
			tweet_id = None
			
			# generate update statements and execute
			stmts = []
			for tweet in tweets:
				scores = self.sent_analyzer.polarity_scores(tweet.text)
				tweet_id = tweet[0]
				"""
				Raw string substitution seems to improve performance by a lot over SQLAlchemy update method.
				Performance bottleneck is here and parameters are internally generated.
				"""
				stmts.append(queries.UPDATE_TWEET_SCORE.format(score=scores['compound'], tweet_id=tweet_id))
			if len(stmts) > 0:
				connection.execute(';'.join(stmts)) 
			
				trans.commit()
			last_id = tweet_id
			"""ID of the last tweet processed (max ID) will determine the range of tweets to compute aggregates for
			and will be set as the last_processed_id at the end of that transaction. None if no tweets updated"""
		return last_id 

	def get_updated_aggregates(self, timestamps, interval=INTERVAL_15MIN):
		"""
		Query for aggregates (2-interval moving average) for any timestamps that have had updates.
		Args:
			timestamps: a list of Unix timestamps of aggregates that were updated
			interval: the interval these aggregates were calculated for
		Returns:
			A dict mapping the timestamp for each updated interval 
			to its moving average sentiment score.
		"""
		if len(timestamps) > 0:
			with self.engine.connect() as connection:
				subtract_interval = INTERVALS[interval]['duration']
				query = text(
					queries.SELECT_AGGREGATES.format(
						interval=interval,
						subtract_interval=subtract_interval
					)
				)
				
				aggregates = connection.execute(query, {'ts_list': tuple(timestamps)})
		else:
			aggregates = []
		return { int(res[0]): res[1] for res in aggregates }

	def store_aggregates(self, start_id, last_id, interval=INTERVAL_15MIN):
		"""
		Computes the aggregate values (e.g., moving average sentiment scores) between start_id and last_id,
		updating the relevant aggre.
		Args:
			start_id: the ID of the first Tweet to process
			last_id: the ID of the last Tweet to procss
			interval: the interval the aggregates were calculated for
		Returns: 
			A dict mapping the timestamp for each updated interval 
			to its moving average sentiment score.
		"""
		with self.engine.connect() as connection:
			"""transaction: update last_processed_id counter only if Tweets 
			after that point have been added to the aggregate rows"""
			with connection.begin() as trans:
				query = queries.SELECT_COMPUTED_AGGREGATES.format(interval=interval)
				aggregates = connection.execute(query, start_id, last_id)
				
				# upsert: if no aggregate row for this timestamp exists, insert; if yes, add to sums
				query = queries.UPSERT_AGGREGATES.format(interval=interval)
				timestamps = set([])
				for (ts, sum_sent, count_sent) in aggregates:
					timestamps.add(ts)
					connection.execute(
						query,
						(ts, sum_sent, count_sent, sum_sent, count_sent)
					)
				connection.execute(queries.UPDATE_LAST_PROCESSED_ID, last_id)
				trans.commit()
			return self.get_updated_aggregates(timestamps, interval=interval)

	def delete_old_aggregates(self):
		"""For 1-second interval, delete aggregates older than an interval"""
		with self.engine.connect() as connection:
			delete_before_ts = arrow.utcnow().replace(seconds=-INTERVALS[INTERVAL_1S]['aggregateMaxAge']).datetime
			connection.execute(
				queries.DELETE_OLD_AGGREGATES,
				delete_before_ts
			)

	def process_tweets(self):
		"""Computes all scores and aggregate values for all new Tweets, and stores them."""
		t0 = time.time()
		last_processed_id = self.get_last_processed_id()
		last_id = self.score_tweets(last_processed_id + 1)
		if last_id is not None:
			update_msg = {}
			for interval in [INTERVAL_15MIN, INTERVAL_1S]:
				values = self.store_aggregates(last_processed_id + 1, last_id, interval=interval)
				update_msg[interval] = values
			self.delete_old_aggregates()
		if self.socket:
			# send an event to notify web app of new data
			self.socket.emit('sentimentUpdate', update_msg, namespace='/rt') 

	@rate_limited(1)
	def rate_limited_process_tweets(self):
		self.process_tweets()

def main():
	logging.basicConfig()
	socketio = SocketIO(message_queue=config.MESSAGE_QUEUE)
	processor = TweetProcessor(engine, socket=socketio)
	last_exec = 0
	while True:
		try:
			processor.rate_limited_process_tweets()
		except sqlalchemy.exc.OperationalError as e:
			logging.exception(e)
			time.sleep(DB_CONNECTION_ERROR_WAIT_TIME)

if __name__ == '__main__':
	main()