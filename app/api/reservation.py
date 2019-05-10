from flask_restful import Resource, abort
from app.models import Event, EventSchema, Schedule, Appointment, User
from .authentication import validate_token

from marshmallow import fields, validate, pprint
from webargs.flaskparser import parser, use_kwargs, use_args


class EventManagement(Resource):
    def get(self, event_id):
        event = Event.query.filter_by(id=event_id).first()

    def put(self, event_id):
        pass

    def delete(self, event_id):
        pass


class EventList(Resource):
    def get(self):
        validate_token()
        event = Event.query.all()
        event_schema = EventSchema(many=True)
        return event_schema.dump(event), 200

    @use_kwargs(EventSchema())
    def post(self, name, description, schedules):
        _, user_id = validate_token()
        new_event = Event(
            name=name,
            description=description
        )
        new_event.provider = User().query.filter_by(id=user_id).first()
        for s in schedules:
            new_schedule = Schedule(start_time=s['start_time'], end_time=s['end_time'])
            new_schedule.save_to_db()
            new_event.schedules.append(new_schedule)
        new_event.save_to_db()

        return {'status': 'success', 'message': 'Successfully created event'}, 200
