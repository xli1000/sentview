(function() {
	angular
		.module('sentview.timeCharts')
		.component('svTimePanel', {
			controller: 'TimePanelController as vm',
			templateUrl: '/js/app/timeCharts/time-panel.component.html'
		});
}());
