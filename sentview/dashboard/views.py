from sqlalchemy import func
from flask import Blueprint, jsonify, render_template
from sentview.shared import dbsession, engine
from sentview.tweet.models import Tweet
import arrow
import string

dashboard = Blueprint('dashboard', __name__, template_folder='templates/build')

intervals = {
	'15min': {
		'defaultStart': {'days': -7},
		'subtract': '15 minutes'
	},
	'1s': {
		'defaultStart': {'minutes': -2},
		'subtract': '1 second'
	}
}

def get_moving_average(start_datetime, interval='15min'):
	subtract_interval = intervals[interval]['subtract']
	query = string.Template("SELECT \
		EXTRACT(epoch FROM agg1.ts) AS ts, \
		(agg1.sum_sent + agg2.sum_sent)/(agg1.count_sent+agg2.count_sent), \
		(agg1.count_sent + agg2.count_sent) \
		FROM tw_agg_$interval agg1 \
		JOIN tw_agg_$interval agg2 ON agg1.ts - INTERVAL '$subtract_interval' = agg2.ts\
		WHERE agg1.ts >= %s \
		ORDER BY ts").substitute(interval=interval, subtract_interval=subtract_interval)
	return engine.execute(query, start_datetime)

@dashboard.route('/')
def index():
	return render_template('index.html')

@dashboard.route('/sentiment')
def sentiment():
	average = [ res[0] for res in engine.execute('SELECT SUM(sum_sent)/SUM(count_sent) FROM tw_agg_15min')][0]
	# simple: SELECT EXTRACT(epoch FROM ts) AS ts, sum_sent/count_sent, count_sent FROM tw_agg_15min WHERE ts > %s ORDER BY ts
	
	return_data = {
		'timeSeries': {},
		'historicalAverage': average 
	}
	
	for interval in ['15min', '1s']:
		start = arrow.utcnow().replace(**intervals[interval]['defaultStart']).datetime
		moving_average  = get_moving_average(
			start,
			interval=interval
		)
		return_data['timeSeries'][interval] = [ 
			{ 'ts': res[0], 'score': res[1] } 
			for res in  moving_average
		]
	
	return jsonify(return_data)
