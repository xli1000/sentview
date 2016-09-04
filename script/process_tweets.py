import sys
import os
import time
sys.path.insert(0, os.path.abspath('..'))

import time
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sentview.tweet.models import Tweet
from sentview.shared import dbsession, engine

sent_analyzer = SentimentIntensityAnalyzer() 
# lexicon must be downloaded first

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
			LIMIT 200
		''', start_id)
	
	trans = connection.begin()
	tweet_id = None
	
	# generate update statements and execute
	stmts = []
	for tweet in tweets:
		scores = sent_analyzer.polarity_scores(tweet.text)
		tweet_id = tweet[0]
		# raw string substitution seems to improve performance by a lot over SQLAlchemy update method
		stmts.append('UPDATE tweet SET sent_score=%f WHERE id=%d' % (scores['compound'], tweet_id))
	connection.execute(';'.join(stmts)) 
	
	trans.commit()
	last_id = tweet_id
	'''ID of the last tweet processed (max ID) will determine the range of tweets to compute aggregates for
	and will be set as the last_processed_id at the end of that transaction'''
	return last_id 

def store_aggregates(start_id, last_id):
	connection = engine.connect()
	
	'''transaction: update last_processed_id counter only if Tweets 
	after that point have been added to the aggregate rows'''
	trans = connection.begin()
	aggregates = connection.execute('''SELECT
		ceil_time_15min(ts) ctime, SUM(sent_score) AS sum_sent, COUNT(*) AS count_sent
		FROM tweet 
		WHERE lang='en' AND id > %s AND id <= %s
		GROUP BY ctime
	''', start_id, last_id)
	
	for (ts, sum_sent, count_sent) in aggregates:
		# upsert: if no aggregate row for this timestamp exists, insert; if yes, add to sums
		connection.execute('''INSERT INTO tw_agg_15min(ts, sum_sent, count_sent)
			VALUES (%s, %s, %s)
			ON CONFLICT (ts) DO UPDATE SET sum_sent = tw_agg_15min.sum_sent + %s, 
			count_sent = tw_agg_15min.count_sent + %s''',
			(ts, sum_sent, count_sent, sum_sent, count_sent)
		)

	connection.execute('UPDATE tw_processing SET last_processed_id=%s', last_id)
	trans.commit()

def process_tweets():
	t0 = time.time()
	last_processed_id = get_last_processed_id()
	last_id = score_tweets(last_processed_id + 1)
	store_aggregates(last_processed_id + 1, last_id)
	print time.time() - t0

def main():
	while True:
		process_tweets()

if __name__ == '__main__':
	main()
