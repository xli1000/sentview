
(function() {
	angular
		.module('sentview.core')
		.factory('socket', socket);
	
	socket.$inject = ['$timeout', 'svSettings'];
	
	function socket($timeout, svSettings) {
		/* socketio wrapper factory from
		 * http://www.html5rocks.com/en/tutorials/frameworks/angular-websockets/ */
		io.transports = ['websocket', 'xhr-polling'];
		
		var socket = io.connect(svSettings.apiRoot + 'rt');
		
		return {
			on: on,
			emit: emit
		};
		
		function on(eventName, callback) {
			socket.on(eventName, function() {
				var args = arguments;
				$timeout(function() {
					callback.apply(socket, args);
				});
			});
		}
		
		function emit(eventName, data, callback) {
			socket.emit(eventName, data, function() {
				var args = arguments;
				$timeout(function() {
					if (callback) {
					  callback.apply(socket, args);
					}
				});
			});
		}
	}
}());
