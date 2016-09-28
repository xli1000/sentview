(function() {
	angular
		.module('sentview.core')
		.factory('termData', termData);

	termData.$inject = ['$resource'];

	function termData($resource) {
		var terms = {};
	 	var termsResource = $resource('/terms');

		return {
			terms: terms,
			load: load
		};


		function load() {
			termsResource.get().$promise.then(function(resource) {
				terms.positive = resource.data.positive;
				terms.negative = resource.data.negative;
			});
		}
	}
}());