from sqlalchemy import func
from flask import Blueprint, jsonify, render_template
from sentview.shared import dbsession
from sentview.tweet.models import Tweet
import arrow

dashboard = Blueprint('dashboard', __name__, template_folder='templates/build')

@dashboard.route('/')
def index():
	return render_template('index.html')

@dashboard.route('/sentiment')
def sentiment():
	prev_time = arrow.utcnow().replace(hours=-2).datetime
	time_unit_expr = 'ROUND(EXTRACT(epoch FROM tweet.ts)/600) AS tunit'
	
	series = [ 
		{ 'ts': res[0], 'score': res[1], 'count': res[2] } 
		for res in (dbsession
			.query(time_unit_expr, func.avg(Tweet.sent_score), func.count(Tweet.id))
			.filter( (Tweet.lang == 'en') & (Tweet.ts > prev_time) & (Tweet.sent_score != None))
			.group_by('tunit')
			.order_by('tunit ASC')
			.all())
		]
	return jsonify({ 'timeSeries': series })
