SELECT_MOVING_AVERAGES_BY_TIMESTAMP = '''
	SELECT
		EXTRACT(epoch FROM agg1.ts) AS ts, 
		(agg1.sum_sent + agg2.sum_sent)/(agg1.count_sent+agg2.count_sent) AS score
		FROM tw_agg_{interval} agg1 
		JOIN tw_agg_{interval} agg2 ON agg1.ts - INTERVAL '{subtract_interval}' = agg2.ts
		WHERE agg1.ts >= %s 
	ORDER BY ts
'''

SELECT_AVERAGE = 'SELECT SUM(sum_sent)/SUM(count_sent) AS average FROM tw_agg_15min'

SELECT_LAST_TERM_DATA = 'SELECT EXTRACT(EPOCH FROM ts) AS ts, data FROM term ORDER BY ts DESC LIMIT 1'