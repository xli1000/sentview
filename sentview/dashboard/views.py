from sqlalchemy import func
from flask import Blueprint, jsonify, render_template
from sentview.shared import dbsession, engine
from sentview.tweet.models import Tweet
import arrow

dashboard = Blueprint('dashboard', __name__, template_folder='templates/build')

@dashboard.route('/')
def index():
	return render_template('index.html')

@dashboard.route('/sentiment')
def sentiment():
	prev_time = arrow.utcnow().replace(days=-7).datetime
	
	
	average = [ res[0] for res in engine.execute('SELECT SUM(sum_sent)/SUM(count_sent) FROM tw_agg_15min')][0]
	# simple: SELECT EXTRACT(epoch FROM ts) AS ts, sum_sent/count_sent, count_sent FROM tw_agg_15min WHERE ts > %s ORDER BY ts
	sent_15min_res = engine.execute('SELECT \
		EXTRACT(epoch FROM agg1.ts) AS ts, \
		(agg1.sum_sent + agg2.sum_sent)/(agg1.count_sent+agg2.count_sent), \
		(agg1.count_sent + agg2.count_sent) \
		FROM tw_agg_15min agg1 \
		JOIN tw_agg_15min agg2 ON EXTRACT(epoch FROM agg1.ts) - 900 = EXTRACT(epoch FROM agg2.ts)\
		WHERE agg1.ts > %s \
		ORDER BY ts', prev_time)
	
	sent_15min = [ 
		{ 'ts': res[0], 'score': res[1], 'count': res[2] } 
		for res in sent_15min_res
		]
	return jsonify({ 'timeSeries': sent_15min, 'historicalAverage': average })
