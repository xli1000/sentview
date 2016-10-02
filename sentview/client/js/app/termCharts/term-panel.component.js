(function() {
	angular
		.module('sentview.termCharts')
		.component('svTermPanel', {
			controller: 'TermPanelController as vm',
			templateUrl: 'js/app/termCharts/term-panel.component.html'
		});
}());
