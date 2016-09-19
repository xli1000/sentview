import cPickle as pickle
import json
import logging
import math
import os
import sys
import time

import arrow
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize.casual import casual_tokenize
import numpy as np
from sklearn.feature_extraction import text as sklearn_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.sql import text

sys.path.insert(0, os.path.abspath('..'))

import queries
from sentview.shared import dbsession, engine

DEFAULT_TFIDF_PATH = 'tfidf.p'
DEFAULT_CORPUS_PATH = 'corpus'
EXTRA_STOP_WORDS = ['don', 'amp','just', 'fucking', 'ur','gonna', 'feel', 'follow']

logger = logging.getLogger(__name__)

def tokenize(text):
	return casual_tokenize(text, strip_handles=True, preserve_case=False)

class TermAnalyzer(object):
	def __init__(self, tfidf_save_path=DEFAULT_TFIDF_PATH, db_engine=engine, corpus_path=DEFAULT_CORPUS_PATH):
		self.tfidf_save_path = tfidf_save_path
		self.corpus_path = corpus_path
		if os.path.isfile(self.tfidf_save_path):
			self.tfidf = self.load_tfidf(save_path=self.tfidf_save_path)
		else:
			self.tfidf = self.create_tfidf()
			self.fit_tfidf(save=True, save_path=self.tfidf_save_path, corpus_path=self.corpus_path)
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

	def fit_tfidf(self, save=False, save_path=DEFAULT_TFIDF_PATH, corpus_path=DEFAULT_CORPUS_PATH):
		for filename in os.listdir(corpus_path):
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
			print resp.nonzero()
			
			top_indices = sorted(list(resp.nonzero()[1]), 
				key=lambda feature_index: -1*resp[0, feature_index])[0:20]
			term_scores = [ (feature_names[index], resp[0, index]) for index in top_indices ]
			term_lists.append(term_scores)

		return term_lists

	def analyze_recent_tweets(self):
		"""Computes lists of significant terms for positive and negative tweets, storing them in a database row"""
		start, end = self.get_recent_interval()
		neg_tweets, pos_tweets = self.get_recent_tweets(start, end)
		term_lists = self.get_term_scores([neg_tweets, pos_tweets])
		data = {}
		for (i, key) in [(0, 'negative'), (1, 'positive')]:
		 	data[key] = { term: score for (term, score) in term_lists[i] }
		json_data = json.dumps(data)
		connection = self.db_engine.connect()
		connection.execute(queries.INSERT_TERM_DATA, end.datetime, json_data, json_data )
		connection.close()

	@staticmethod
	def get_recent_interval(shift=-60, interval_size=900):
		"""parameters in seconds"""
		end = arrow.get(int(math.ceil( (time.time() + shift) / interval_size)) * interval_size)
		start = end.replace(seconds=-interval_size)
		return start, end
				
	def get_recent_tweets(self, start, end):
		connection = self.db_engine.connect()
		neg_tweets = []
		pos_tweets = []
		for (compare_sign, threshold) in [('>', 0.15), ('<', -0.15)]:
			query = queries.SELECT_TWEETS_BY_TIME_RANGE_AND_SCORE.format(compare_sign=compare_sign, threshold=threshold)
			tweets = [ result['text'] for result in connection.execute(text(query), {'start':start.datetime, 'end': end.datetime}) ]
			if compare_sign == '>':
				pos_tweets = tweets
			else:
				neg_tweets = tweets 
		connection.close()
		return neg_tweets, pos_tweets

if __name__ == '__main__':
	logging.basicConfig()
	term_analyzer = TermAnalyzer()
	term_analyzer.analyze_recent_tweets()