import sys
import os
import time
from ratelimit import rate_limited
import arrow
from sqlalchemy.sql import text
from flask_socketio import SocketIO, emit
import string

sys.path.insert(0, os.path.abspath('..'))

import time
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sentview.tweet.models import Tweet
from sentview.shared import dbsession, engine

sent_analyzer = SentimentIntensityAnalyzer() 
# lexicon must be downloaded first

socketio = SocketIO(message_queue='redis://')

MAX_BATCH_SIZE = 400

def get_last_processed_id():
	results = [
		row for row in 
		engine.execute('SELECT last_processed_id FROM tw_processing') 
	]
	return results[0][0]

def score_tweets(start_id):
	connection = engine.connect()
	tweets = connection.execute('''
		SELECT id, text
			FROM tweet 
			WHERE id >= %s AND lang=\'en\'
			ORDER BY id ASC
			LIMIT %s
		''', start_id, MAX_BATCH_SIZE)
	
	trans = connection.begin()
	tweet_id = None
	
	# generate update statements and execute
	stmts = []
	for tweet in tweets:
		scores = sent_analyzer.polarity_scores(tweet.text)
		tweet_id = tweet[0]
		# raw string substitution seems to improve performance by a lot over SQLAlchemy update method
		stmts.append('UPDATE tweet SET sent_score=%f WHERE id=%d' % (scores['compound'], tweet_id))
	if len(stmts) > 0:
		connection.execute(';'.join(stmts)) 
	
		trans.commit()
	last_id = tweet_id
	'''ID of the last tweet processed (max ID) will determine the range of tweets to compute aggregates for
	and will be set as the last_processed_id at the end of that transaction. None if no tweets updated'''
	connection.close()
	return last_id 

def get_updated_aggregates(timestamps, interval='15min'):
	'''query for aggregates (2-interval moving average) for any timestamps that have had updates'''
	if len(timestamps) > 0:
		connection = engine.connect()
		subtract_interval = { '1s': '1 second', '15min': '15 minutes' }[interval]
		query = text(
			string.Template('''SELECT
				EXTRACT(epoch FROM agg1.ts) AS ts,
				(agg1.sum_sent + agg2.sum_sent)/(agg1.count_sent+agg2.count_sent),
				(agg1.count_sent + agg2.count_sent)
				FROM tw_agg_$interval agg1
				JOIN tw_agg_$interval agg2 ON agg1.ts - INTERVAL '$subtract_interval' = agg2.ts\
				WHERE agg1.ts IN :ts_list''').substitute(
					interval=interval, subtract_interval=subtract_interval
				)
		)
		
		aggregates = connection.execute(query, {'ts_list': tuple(timestamps)})
		connection.close()
	else:
		aggregates = []
	return { int(res[0]): res[1] for res in aggregates }

def store_aggregates(start_id, last_id, interval='15min'):
	connection = engine.connect()
	
	'''transaction: update last_processed_id counter only if Tweets 
	after that point have been added to the aggregate rows'''
	trans = connection.begin()
	query = '''SELECT
		ceil_time_$interval(ts) ctime, SUM(sent_score) AS sum_sent, COUNT(*) AS count_sent
		FROM tweet 
		WHERE lang='en' AND id > %s AND id <= %s
		GROUP BY ctime
	'''.replace('$interval', interval)
	aggregates = connection.execute(query, start_id, last_id)
	
	
	# upsert: if no aggregate row for this timestamp exists, insert; if yes, add to sums
	query = '''INSERT INTO tw_agg_$interval(ts, sum_sent, count_sent)
			VALUES (%s, %s, %s)
			ON CONFLICT (ts) DO UPDATE SET sum_sent = tw_agg_$interval.sum_sent + %s, 
			count_sent = tw_agg_$interval.count_sent + %s'''.replace('$interval', interval)
	timestamps = set([])
	for (ts, sum_sent, count_sent) in aggregates:
		timestamps.add(ts)
		connection.execute(
			query,
			(ts, sum_sent, count_sent, sum_sent, count_sent)
		)
	if interval == '1s':
		connection.execute('DELETE FROM tw_agg_1s WHERE ts < %s',
			arrow.utcnow().replace(minutes=-30).datetime)

	connection.execute('UPDATE tw_processing SET last_processed_id=%s', last_id)
	trans.commit()
	connection.close()
	return get_updated_aggregates(timestamps, interval=interval)

@rate_limited(1)
def process_tweets():
	t0 = time.time()
	last_processed_id = get_last_processed_id()
	last_id = score_tweets(last_processed_id + 1)
	if last_id is not None:
		update_msg = {}
		for interval in ['15min', '1s']:
			values = store_aggregates(last_processed_id + 1, last_id, interval=interval)
			update_msg[interval] = values
		socketio.emit('sentimentUpdate', update_msg, namespace='/rt')
	#print time.time() - t0

def main():
	last_exec = 0
	while True:
		process_tweets()

if __name__ == '__main__':
	main()
