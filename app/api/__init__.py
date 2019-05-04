from flask import Blueprint
from flask_restful import Api

from .authentication import Registration, Login, Logout

api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint)

api.add_resource(Registration, '/registration')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
