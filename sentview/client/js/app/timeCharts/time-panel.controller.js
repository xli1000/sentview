(function() {
	angular
		.module('sentview.timeCharts')
		.controller('TimePanelController', TimePanelController);
	
	TimePanelController.$inject = ['sentimentData'];
	
	function TimePanelController(sentimentData) {
		sentimentData.loadSentiment()
			.then(
				null,
				function() { /*error*/ }
			);
		
		var vm = this;
		
		vm.timeSeries = sentimentData.timeSeries;
		vm.summary = sentimentData.summary;
		
	}
}());
