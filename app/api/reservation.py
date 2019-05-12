from flask_restful import Resource, abort
from marshmallow import pprint
from sqlalchemy.orm import lazyload

from app import db
from app.models import Event, EventSchema, Schedule, Appointment, AppointmentSchema
from .authentication import validate_token
from webargs.flaskparser import use_kwargs


class EventManagement(Resource):
    def get(self, event_id):
        validate_token()

        event = Event.query.get(event_id)
        if not event:
            abort(400, status='fail', message='Invalid event id')

        return EventSchema().dump(event), 200

    def put(self, event_id):
        validate_token()
        abort(501, status='fail', message='Just delete and recreate')

    def delete(self, event_id):
        _, user_id = validate_token()

        event = Event.query.get(event_id)
        if not event:
            abort(400, status='fail', message='Invalid event id')
        if event.provider_id != user_id:
            abort(403, status='fail', message='Nice try')

        db.session.delete(event)
        db.session.commit()

        return {'status': 'success', 'message': 'Successfully deleted event'}, 200


class EventList(Resource):
    def get(self):
        validate_token()
        event = Event.query.all()  # eager loading
        event_schema = EventSchema(many=True, exclude=('schedules.appointments.event',))
        return event_schema.dump(event), 200

    @use_kwargs(EventSchema())
    def post(self, name, description, schedules):
        _, user_id = validate_token()

        new_schedules = [Schedule(start_time=s['start_time'], end_time=s['end_time']) for s in schedules]
        new_event = Event(name=name, description=description, provider_id=user_id, schedules=new_schedules)
        new_event.save_to_db()
        # https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/#simple-relationships

        return {'status': 'success', 'message': 'Successfully created event'}, 200


class AppointmentManagement(Resource):
    def get(self, appointment_id):
        pass

    def put(self, appointment_id):
        pass

    def delete(self, appointment_id):
        pass


class AppointmentList(Resource):
    def get(self):
        _, user_id = validate_token()

        appointments = Appointment.query.filter_by(booker_id=user_id).all()
        # appointments = User.query.get(user_id).appointments  # lazy loading
        for a in appointments:
            pprint(a.schedule.event)
        appointment_schema = AppointmentSchema(many=True, exclude=('booker',))

        return appointment_schema.dump(appointments), 200

    @use_kwargs(AppointmentSchema())
    def post(self, schedule_id, message, start_time, end_time):
        _, user_id = validate_token()

        schedule = Schedule.query.options(lazyload('appointments')).get(schedule_id)
        if not schedule:
            abort(400, status='fail', message='Invalid schedule id')
        if start_time < schedule.start_time or end_time > schedule.end_time:
            abort(400, status='fail', message='Inappropriate time')
        if Schedule.check_conflict(start_time, end_time, schedule.appointments):
            abort(400, status='fail', message='Conflicting reservation')

        schedule.appointments.append(
            Appointment(
                start_time=start_time, end_time=end_time, message=message, booker_id=user_id))
        schedule.save_to_db()

        return {'status': 'success', 'message': 'Successfully created appointment'}, 200
