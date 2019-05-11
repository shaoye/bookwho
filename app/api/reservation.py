from flask_restful import Resource, abort
from app import db
from app.models import Event, EventSchema, Schedule, Appointment, User, AppointmentSchema
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
        event = Event.query.all()
        event_schema = EventSchema(many=True)
        return event_schema.dump(event), 200

    @use_kwargs(EventSchema())
    def post(self, name, description, schedules):
        _, user_id = validate_token()

        new_schedules = [Schedule(start_time=s['start_time'], end_time=s['end_time']) for s in schedules]
        new_event = Event(name=name, description=description, provider_id=user_id, schedules=new_schedules)
        db.session.add_all(new_schedules + [new_event])
        db.session.commit()

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

        current_user = User.query.get(user_id)
        appointments = current_user.appointments
        # appointments = Appointment.query.with_parent(current_user).all()

        appointment_schema = AppointmentSchema(many=True)

        return appointment_schema.dump(appointments), 200

    def post(self):
        pass
