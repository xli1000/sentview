import os

import eventlet
eventlet.monkey_patch()

from sentview import create_app, socketio

app = create_app()

if __name__ == '__main__':
	debug = os.environ.get('SENTVIEW_ENV') != 'PROD'
	socketio.run(app, debug=debug, port=9000)
