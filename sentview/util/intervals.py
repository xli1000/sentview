INTERVAL_1S = '1s'
INTERVAL_15MIN = '15min'

INTERVALS = {
	INTERVAL_15MIN: {
		'defaultStart': {'days': -7},  # default range of data to show for this interval
		'duration': '15 minutes'  # size of interval for Postgres interval
	},
	INTERVAL_1S: {
		'defaultStart': {'minutes': -2},
		'duration': '1 second',
		'aggregateMaxAge': 1800 
	}
}