SELECT_LAST_PROCESSED_ID = 'SELECT last_processed_id FROM tw_processing'
SELECT_TWEETS = '''
	SELECT id, text
		FROM tweet 
		WHERE id >= %s AND lang=\'en\'
		ORDER BY id ASC
		LIMIT %s
'''
UPDATE_TWEET_SCORE = 'UPDATE tweet SET sent_score={score} WHERE id={tweet_id}'

SELECT_AGGREGATES = '''
	SELECT
		EXTRACT(epoch FROM agg1.ts) AS ts,
		(agg1.sum_sent + agg2.sum_sent)/(agg1.count_sent+agg2.count_sent) AS score,
		(agg1.count_sent + agg2.count_sent)
	FROM tw_agg_{interval} agg1
	JOIN tw_agg_{interval} agg2 ON agg1.ts - INTERVAL '{subtract_interval}' = agg2.ts\
	WHERE agg1.ts IN :ts_list
'''
SELECT_COMPUTED_AGGREGATES = '''
	SELECT
		ceil_time_{interval}(ts) ctime, SUM(sent_score) AS sum_sent, COUNT(*) AS count_sent
	FROM tweet 
	WHERE lang='en' AND id > %s AND id <= %s
	GROUP BY ctime
'''

UPSERT_AGGREGATES = '''
	INSERT INTO tw_agg_{interval}(ts, sum_sent, count_sent)
	VALUES (%s, %s, %s)
	ON CONFLICT (ts) DO UPDATE SET sum_sent = tw_agg_{interval}.sum_sent + %s, 
	count_sent = tw_agg_{interval}.count_sent + %s
'''

DELETE_OLD_AGGREGATES = '''DELETE FROM tw_agg_1s WHERE ts < %s'''

UPDATE_LAST_PROCESSED_ID = 'UPDATE tw_processing SET last_processed_id=%s'

INSERT_TERM_DATA = '''
	INSERT INTO term(ts, data) VALUES (%s, %s)
	ON CONFLICT (ts) DO UPDATE SET data = %s
'''

SELECT_TWEETS_BY_TIME_RANGE_AND_SCORE = '''
	SELECT text
	FROM tweet 
	WHERE lang=\'en\'
		AND sent_score {compare_sign} {threshold}
		AND ts > :start 
		AND ts < :end
'''