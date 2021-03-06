import json

import arrow
from flask import Blueprint, jsonify, render_template, current_app
from sqlalchemy import func

import queries
from sentview.shared import dbsession, engine
from sentview.tweet.models import Tweet
import sentview.util.errors
from sentview.util.intervals import INTERVAL_15MIN, INTERVAL_1S, INTERVALS

dashboard = Blueprint('dashboard', __name__, template_folder='templates/build')

def get_moving_averages(start_datetime, interval=INTERVAL_15MIN):
	subtract_interval = INTERVALS[interval]['duration']
	query = queries.SELECT_MOVING_AVERAGES_BY_TIMESTAMP.format(interval=interval, subtract_interval=subtract_interval)
	results = engine.execute(query, start_datetime)
	return [ 
		{ 'ts': res['ts'], 'score': res['score'] } 
		for res in results
	]

def get_average():
	res = engine.execute(queries.SELECT_AVERAGE).fetchone()
	if res is None:
		return None
	else:
		return res['average']

def get_terms():
	res = engine.execute(queries.SELECT_LAST_TERM_DATA).fetchone()
	if res is None:
		return {}
	serializable_data = { 'ts': res['ts'], 'data': res['data'] } 
	return serializable_data

@dashboard.route('/')
def index():
	"""Main page"""
	print dir(current_app.config)
	return render_template('index.html', base_url_path=current_app.config['BASE_URL_PATH'])

@dashboard.route('/sentiment')
def sentiment():
	"""Return sentiment data over time"""
	average = get_average()
	return_data = {
		'timeSeries': {},
		'historicalAverage': average
	}
	
	for interval in [INTERVAL_15MIN, INTERVAL_1S]:
		start = arrow.utcnow().replace(**INTERVALS[interval]['defaultStart']).datetime
		moving_averages  = get_moving_averages(
			start,
			interval=interval
		)
		return_data['timeSeries'][interval] = moving_averages

	return jsonify(return_data)

@dashboard.route('/terms')
def terms():
	"""Return significant terms for recent negative and positive tweets"""
	terms = get_terms()
	return jsonify(terms)

@dashboard.route('/status')
def status():
	data = {}
	with engine.connect() as connection:
		for (key, query) in [('last_tweet_ts', queries.SELECT_LAST_TWEET_TS), ('last_scored_ts', queries.SELECT_LAST_SCORED_TS)]:
			result = engine.execute(queries.SELECT_LAST_TWEET_TS).fetchone()
			if result is not None:
				data[key] = result[0]
			else:
				data[key] = None
	return jsonify(data)
