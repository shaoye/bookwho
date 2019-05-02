from flask import Flask
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

    from .auth import auth_blueprint as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
