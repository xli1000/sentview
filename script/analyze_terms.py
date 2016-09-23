import cPickle as pickle
import json
import logging
import math
import os
import sys
import time

import arrow
import click
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize.casual import casual_tokenize
import numpy as np
from sklearn.feature_extraction import text as sklearn_text
from sklearn.feature_extraction.text import TfidfVectorizer
import sqlalchemy.exc
from sqlalchemy.sql import text

sys.path.insert(0, os.path.abspath('..'))

import queries
from sentview.shared import dbsession, engine

DEFAULT_TFIDF_PATH = 'tfidf.p'
DEFAULT_CORPUS_PATH = 'corpus'
EXTRA_STOP_WORDS = ['don', 'amp','just', 'fucking', 'ur','gonna', 'feel', 'follow']
DEFAULT_INTERVAL_SIZE = 900 # seconds
TERM_COUNT = 30 # number of top terms to save

# approx. bottom and top quintiles of sentiment score
NEGATIVE_THRESHOLD = -0.15  
POSITIVE_THRESHOLD = 0.5    


logger = logging.getLogger(__name__)

def tokenize(text):
	return casual_tokenize(text, strip_handles=True, preserve_case=False)

class TermAnalyzer(object):
	def __init__(self, tfidf_save_path=DEFAULT_TFIDF_PATH, 
				db_engine=engine, corpus_path=DEFAULT_CORPUS_PATH):
		self.tfidf_save_path = tfidf_save_path
		self.corpus_path = corpus_path
		self.db_engine = db_engine
	
	@staticmethod
	def load_tfidf(save_path=DEFAULT_TFIDF_PATH):
		with open(save_path) as f:
			tfidf = pickle.load(f)
			return tfidf

	@staticmethod
	def create_tfidf():
		sent_analyzer = SentimentIntensityAnalyzer() 
		sent_words = sent_analyzer.lexicon.keys()
		stop_words = sklearn_text.ENGLISH_STOP_WORDS.union(sent_words)
		stop_words = stop_words.union(EXTRA_STOP_WORDS)
		return TfidfVectorizer(
			analyzer='word',
			stop_words=stop_words,
			sublinear_tf=True,
			tokenizer=tokenize,
			min_df=2
		)

	def load_or_create_tfidf(self):
		if os.path.isfile(self.tfidf_save_path):
			self.tfidf = self.load_tfidf(save_path=self.tfidf_save_path)
		else:
			self.tfidf = self.create_tfidf()
			self.fit_tfidf(save=True, save_path=self.tfidf_save_path, corpus_path=self.corpus_path)

	def fit_tfidf(self, save=False, save_path=DEFAULT_TFIDF_PATH, corpus_path=DEFAULT_CORPUS_PATH):
		try:
			filenames = os.listdir(corpus_path)
		except OSError as e:
			logger.error('Error listing directory.')
			raise e

		for filename in filenames:
			filepath = os.path.join(corpus_path, filename)
			try:
				with open(filepath) as f:
					self.tfidf.fit_transform([line for line in f])
			except ValueError as err:
				logger.warning('Could not fit document: {filename}'.format(filename=filename))
				logger.exception(err)
		
		if save:
			with open(save_path, 'w') as f:
				pickle.dump(self.tfidf ,f)
		
	def get_term_scores(self, tweet_lists):
		"""return a list of the sorted list of top terms with scores for each list of tweets in tweet_lists"""
		term_lists = []
		feature_names = self.tfidf.get_feature_names()
		for tweets in tweet_lists:
			resp = self.tfidf.transform([''.join(tweets)])
			
			indices = sorted(
				list(resp.nonzero()[1]), 
				key=lambda feature_index: -1 * resp[0, feature_index]
			)
			term_scores = [ 
				(feature_names[index], resp[0, index]) 
				for index in indices 
				if len(feature_names[index]) > 1 and 'https:' not in feature_names[index]
			][0:TERM_COUNT]
			term_lists.append(term_scores)

		return term_lists

	def analyze_tweets(self, ts=None):
		"""
		Computes lists of significant terms for positive and negative tweets, storing them in a database row
		Args
			ts: Time to 
		"""
		start, end = self.get_interval(ts=ts)
		neg_tweets, pos_tweets = self.get_tweets_in_range(start, end)
		term_lists = self.get_term_scores([neg_tweets, pos_tweets])
		if len(term_lists[0]) + len(term_lists[1]) > 0:
			data = {}
			for (i, key) in [(0, 'negative'), (1, 'positive')]:
			 	data[key] = { term: score for (term, score) in term_lists[i] }
			json_data = json.dumps(data)
			connection = self.db_engine.connect()
			connection.execute(queries.INSERT_TERM_DATA, end.datetime, json_data, json_data )
			connection.close()
		else:
			logger.warn('No terms')

	@staticmethod
	def get_interval(ts=None, shift=-60, interval_size=DEFAULT_INTERVAL_SIZE):
		"""
		Returns interval start and end times (arrow) based on a time specificied by ts.
		If ts is None, base interval on present. Gets the last whole interval containing ts - shift
		Parameters in seconds
		"""
		if ts is None:
			ts = time.time()
		end_ts = int(math.ceil( (float(ts) + shift) / interval_size) ) * interval_size
		end = arrow.get(end_ts)
		start = end.replace(seconds=-interval_size)
		return start, end
				
	def get_tweets_in_range(self, start, end):
		connection = self.db_engine.connect()
		neg_tweets = []
		pos_tweets = []
		for (compare_sign, threshold) in [('>', POSITIVE_THRESHOLD), ('<', NEGATIVE_THRESHOLD)]:
			query = (queries.SELECT_TWEETS_BY_TIME_RANGE_AND_SCORE
						.format(compare_sign=compare_sign, threshold=threshold))
			tweets = [ 
				result['text'] for result in 
				connection.execute(text(query), {'start':start.datetime, 'end': end.datetime}) 
			]
			if compare_sign == '>':
				pos_tweets = tweets
			else:
				neg_tweets = tweets 
		connection.close()
		return neg_tweets, pos_tweets

@click.command()
@click.option('--loop/--no-loop', default=False)
@click.option('--run-interval', default=300,
				 help='Run every this number of seconds')
@click.option('--corpus-path', default=DEFAULT_CORPUS_PATH)
@click.option('--start-time', type=float, default=None, 
				help=('If specified, compute for this time instead of present.'
				'Otherwise, use the present. Unix timestamp'))
def main(run_interval=300, 
		loop=False, 
		corpus_path=DEFAULT_CORPUS_PATH, 
		start_time=None):
	term_analyzer = TermAnalyzer(corpus_path=corpus_path)
	term_analyzer.load_or_create_tfidf()
	ts = start_time 
	while True:
		try:
			term_analyzer.analyze_tweets(ts=ts)
		except sqlalchemy.exc.OperationalError as e:
			logger.error('Problem with database connection.')
			logger.exception(e)

		if not loop:
			break
		elif ts is not None:
			# if not using the present, calculate the time for the next interval
			ts += DEFAULT_INTERVAL_SIZE
		time.sleep(run_interval -  time.time() % run_interval )

if __name__ == '__main__':
	logging.basicConfig()
	main()