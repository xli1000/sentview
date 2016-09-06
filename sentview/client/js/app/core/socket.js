
(function() {
	angular
		.module('sentview.core')
		.factory('socket', socket);
	
	socket.$inject = ['$rootScope'];
	
	function socket($rootScope) {
		/* socketio wrapper factory from
		 * http://www.html5rocks.com/en/tutorials/frameworks/angular-websockets/ */
		io.transports = ['websocket', 'xhr-polling'];
		var socket = io.connect('/rt');
		return {
			on: function(eventName, callback) {
				socket.on(eventName, function() {
					var args = arguments;
					$rootScope.$apply(function() {
						callback.apply(socket, args);
					});
				});
			},
			emit: function(eventName, data, callback) {
				socket.emit(eventName, data, function() {
					var args = arguments;
					$rootScope.$apply(function() {
						if (callback) {
						  callback.apply(socket, args);
						}
					});
				});
			}
		};
	}
})();
