'use strict';

(function() {
	angular.module('sentview.core', []);
	angular.module('sentview.timeCharts', ['sentview.core']);
	angular.module('sentview.dashboard', ['sentview.timeCharts']);
}());
