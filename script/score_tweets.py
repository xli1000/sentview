import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import time
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sentview.tweet.models import Tweet
from sentview.shared import dbsession

BATCH_SIZE = 100
DONE_WAIT_TIME = 30

sent_analyzer = SentimentIntensityAnalyzer() 
# lexicon must be downloaded first

def main():
	while True:
		tweets = (
			dbsession.query(Tweet)
			.filter(Tweet.sent_score==None, Tweet.lang=='en')
			.order_by(Tweet.ts.desc()).limit(BATCH_SIZE)
			.all()
		)
		if len(tweets) == 0: # if no more tweets to score, wait some time
			time.sleep(DONE_WAIT_TIME)
			
		for tweet in tweets:
			scores = sent_analyzer.polarity_scores(tweet.text)
			tweet.sent_score = scores['compound']
			
		dbsession.commit()
	
if __name__ == '__main__':
	main()
