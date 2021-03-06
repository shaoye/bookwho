from flask import Blueprint
from flask_restful import Api

from .authentication import Registration, Login, Logout
from .reservation import EventList, EventManagement
from .reservation import AppointmentList, AppointmentManagement

api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint)

api.add_resource(Registration, '/registration')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')

api.add_resource(EventList, '/event')
api.add_resource(EventManagement, '/event/<event_id>')

api.add_resource(AppointmentList, '/appointment')
api.add_resource(AppointmentManagement, '/appointment/<appointment_id>')
