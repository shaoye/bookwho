from flask_restful import Resource, abort
from app.models import Event, Schedule, Appointment


class EventManagement(Resource):
    def get(self, event_id):
        pass

    def put(self, event_id):
        pass

    def delete(self, event_id):
        pass


class EventList(Resource):
    def get(self):
        pass

    def post(self):
        pass
