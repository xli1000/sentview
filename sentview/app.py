from flask import Flask
from config import config
import os

from shared import socketio

if os.environ.get('LOG_SQL')=='true':
	import logging
	logging.basicConfig()
	logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def create_app(app_name='sentview', config=config):
	app = Flask(app_name, static_folder='client', static_url_path='')
	app.config.from_object(config)
	
	register_blueprints(app)
	socketio.init_app(app, message_queue=config.MESSAGE_QUEUE)
	return app


def register_blueprints(app):
	from dashboard import dashboard
	
	for bp in [dashboard]:
		app.register_blueprint(bp)
