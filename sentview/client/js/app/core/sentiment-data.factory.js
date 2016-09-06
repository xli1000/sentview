(function() {
	angular
		.module('sentview.core')
		.factory('sentimentData', sentimentData);
	
	sentimentData.$inject = ['$http', 'socket', '$rootScope'];
	
	function sentimentData($http, socket, $rootScope) {
		var intervals = ['15min', '1s'];
		
		/* For each interval size, keep an array of points
		 * e.g., { '15min': [ {ts:  1472508000, score: 0.1} ] }
		 */
		var timeSeriesArrays = {};
		
		/* For each interval size, also keep a map from timestamp (s) to data. 
		 * For efficient update of value by timestamp
		 * e.g., { '15min': { 1472508000: { score: 0.1 } } }
		 */
		var timeSeriesTimestampMap = {}; 
		var summary = {};
		
		loadSentiment().then(function() {
			socket.on('sentimentUpdate', onSentimentUpdate);
		});
		
		function loadSentiment() {
			return $http.get('/sentiment')
				.then(function(resp) {
					_.merge(timeSeriesArrays, resp.data.timeSeries);
					generateTimestampMap();
					summary.historicalAverage = resp.data.historicalAverage;
				});
		}
		
		function generateTimestampMap() {
			intervals.forEach(function(interval) {
				if (timeSeriesArrays[interval]) {
					timeSeriesTimestampMap[interval] = {};
					for (var i=0; i < timeSeriesArrays[interval].length; i++) {
						var datum = timeSeriesArrays[interval][i];
						timeSeriesTimestampMap[interval][datum.ts] = datum;
					};
				}
			});
		}
		
		function insertValueIntoArrays(interval, datum) {
			var insertionIndex = _.sortedIndexBy(timeSeriesArrays[interval], 
				datum, 
				function(d) { return d.ts; }
			);
			timeSeriesArrays[interval].splice(insertionIndex, 0, datum);
			timeSeriesArrays[interval].shift();
		}
		
		function onSentimentUpdate(data) {
			intervals.forEach(function(interval) {
				_.forIn(data[interval], function(score, timestamp) {
					var datum = { score: score, ts: parseInt(timestamp) };
					//if this timestamp hasn't been encountered before, insert it into the array
					if (timeSeriesTimestampMap[interval][datum.ts] === undefined) {
						insertValueIntoArrays(interval, datum);
						timeSeriesTimestampMap[interval][datum.ts] = datum;
					} else {
						//add/update value in map
						_.merge(timeSeriesTimestampMap[interval][datum.ts], datum);
					}
				});
			});
		}
		
		return {
			timeSeries: timeSeriesArrays,
			summary: summary
		};
	}
})();
