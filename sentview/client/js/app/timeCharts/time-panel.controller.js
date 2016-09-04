(function() {
	angular
		.module('sentview.timeCharts')
		.controller('TimePanelController', TimePanelController);
	
	TimePanelController.$inject = ['sentimentData'];
	
	function TimePanelController(sentimentData) {
		var vm = this;
		
		vm.timeSeries = sentimentData.timeSeries;
		
	}
})();