from flask import Flask, jsonify
from config import config
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# extensions
# https://flask-marshmallow.readthedocs.io/en/latest/
db = SQLAlchemy()
ma = Marshmallow()


def create_app(config_name='default'):
    app = Flask(__name__)

    cfg = config[config_name]
    app.config.from_object(cfg)
    cfg.init_app(app)

    db.init_app(app)
    ma.init_app(app)

    from .api import api_blueprint
    app.register_blueprint(api_blueprint)

    @app.route('/')
    def index():
        return jsonify({'message': 'Hello world!'}), 200

    @app.before_first_request
    def create_tables():
        db.drop_all()
        db.create_all()

    return app
