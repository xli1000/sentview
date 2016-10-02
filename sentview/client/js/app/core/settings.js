(function() {
	

	angular
		.module('sentview.core')
		.constant('svSettings', getSettings());


	function getSettings() {
		return {
			apiRoot: document.getElementById('url-base').getAttribute('href')
		};
	}

}());