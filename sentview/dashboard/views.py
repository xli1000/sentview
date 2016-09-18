import arrow
from flask import Blueprint, jsonify, render_template
from sqlalchemy import func

import queries
from sentview.shared import dbsession, engine
from sentview.tweet.models import Tweet
from sentview.util.intervals import INTERVAL_15MIN, INTERVAL_1S, INTERVALS

dashboard = Blueprint('dashboard', __name__, template_folder='templates/build')

def get_moving_averages(start_datetime, interval=INTERVAL_15MIN):
	subtract_interval = INTERVALS[interval]['duration']
	query = queries.SELECT_MOVING_AVERAGES_BY_TIMESTAMP.format(interval=interval, subtract_interval=subtract_interval)
	results = engine.execute(query, start_datetime)
	return [ 
		{ 'ts': res[0], 'score': res[1] } 
		for res in results
	]

def get_average():
	results = engine.execute(queries.SELECT_AVERAGE)
	average = [ res[0] for res in results ][0]
	return average

@dashboard.route('/')
def index():
	"""Main page"""
	return render_template('index.html')

@dashboard.route('/sentiment')
def sentiment():
	"""Return the main page."""
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