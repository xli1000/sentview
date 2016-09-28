'use strict';

(function() {
	angular.module('sentview.core', ['ngResource']);
	angular.module('sentview.timeCharts', ['sentview.core']);
	angular.module('sentview.termCharts', ['sentview.core']);
	angular.module('sentview.dashboard', ['sentview.timeCharts', 'sentview.termCharts']);
}());
