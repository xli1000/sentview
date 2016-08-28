(function() {
	angular
		.module('sentview.core')
		.factory('sentimentData', sentimentData);
	
	sentimentData.$inject = ['$http'];
	
	function sentimentData($http) {
		var timeSeries = {};
		
		loadSentiment('10sec');
			
		function loadSentiment(interval) {
			return $http.get('/sentiment?interval=' + interval)
				.then(function(resp) {
					timeSeries[interval] = resp.data.timeSeries;
				});
		}
		
		return {
			timeSeries: timeSeries
		};
	}
})();
