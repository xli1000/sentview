(function() {
	angular
		.module('sentview.termCharts')
		.controller('TermPanelController', TermPanelController);
	
	TermPanelController.$inject = ['termData'];
	
	function TermPanelController(termData) {
		termData.load();
		
		var vm = this;
		vm.terms = termData.terms;
		
	}
}());