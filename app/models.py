from datetime import datetime, timedelta

import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import Schema, fields, validates_schema, ValidationError
from . import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # https://docs.sqlalchemy.org/en/13/core/defaults.html#python-executed-functions
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)  # not utcnow()

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    events = db.relationship(
        'Event',
        backref='provider',
        cascade='all, delete-orphan',
        lazy=True,
        order_by='desc(Event.date_created)'
    )

    appointments = db.relationship(
        'Appointment',
        backref='booker',
        cascade='all, delete-orphan',
        lazy=True,
        order_by='desc(Appointment.start_time)'
    )

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    def encode_token(self, secret):
        payload = {
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'iat': datetime.utcnow(),
            'sub': self.id
        }
        # https://stackoverflow.com/questions/32017527/access-config-values-in-flask-from-other-files
        return jwt.encode(
            payload,
            secret,
            algorithm='HS256'
        ).decode()  # 坑

    @staticmethod
    def decode_token(token, secret):
        try:
            payload = jwt.decode(token, secret)
            return 'Success', payload
        except jwt.ExpiredSignatureError:
            return 'Signature expired.', None
        except jwt.InvalidTokenError:
            return 'Invalid token.', None


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    # bind `role` attribute to `User`
    users = db.relationship('User', backref='role', lazy=True)

    @staticmethod
    def insert_roles():
        roles = ['Student', 'Teacher', 'Administrator']
        for r in roles:
            if Role.query.filter_by(name=r).first():
                continue
            db.session.add(Role(name=r))
        db.session.commit()


class BlacklistToken(db.Model):
    __tablename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(255), nullable=False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def has_token(token):
        res = BlacklistToken.query.filter_by(token=token).first()
        if not res:
            return False
        return True


class Event(db.Model):  # eg:  Office Hour / Meetings
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text())  # description by event provider
    date_created = db.Column(
        db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    schedules = db.relationship(
        'Schedule',
        backref='event',
        cascade='all, delete-orphan',
        lazy=False,  # Eager Loading
        order_by='desc(Schedule.start_time)'
    )

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()


class Schedule(db.Model):  # eg: 6月4日-8点到12点 / 6月5日-14点到18点
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime(), nullable=False)

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))

    appointments = db.relationship(
        'Appointment',
        backref='schedule',
        cascade='all, delete-orphan',
        lazy=False,  # Eager Loading
        order_by='Appointment.start_time'
    )

    # https://docs.sqlalchemy.org/en/13/orm/cascades.html#cascades

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_conflict(start, end, appointments=None):
        if not appointments:
            return False
        last_valid_start = start
        for a in appointments:
            if end < a.start_time and start > last_valid_start:
                return False
            last_valid_start = a.end_time
        if start > last_valid_start:
            return False
        return True


class Appointment(db.Model):  # eg: 6月4日 8.30到9.30
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.Text())  # booker's message to provider
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime(), nullable=False)

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    booker_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()


class RoleSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    date_created = fields.DateTime(dump_only=True)
    role = fields.Nested(RoleSchema, only=('name',))
    # https://marshmallow.readthedocs.io/en/3.0/nesting.html#specifying-which-fields-to-nest


class AppointmentSchema(Schema):
    id = fields.Int(dump_only=True)  # read-only
    schedule_id = fields.Int(required=True, load_only=True)
    message = fields.Str(missing='')
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    booker = fields.Nested(UserSchema, only=('email',), dump_only=True)
    # https://marshmallow.readthedocs.io/en/3.0/quickstart.html#specifying-attribute-names
    event = fields.Nested(
        'EventSchema', only=('name', 'provider', 'description'), dump_only=True, attribute='schedule.event')

    #  https://marshmallow.readthedocs.io/en/3.0/extending.html#schema-level-validation
    @validates_schema
    def check_date_validation(self, data):
        if data['start_time'] >= data['end_time']:
            raise ValidationError('Start must be earlier than End')


class ScheduleSchema(Schema):
    id = fields.Int(dump_only=True)  # read-only
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    # https://marshmallow.readthedocs.io/en/3.0/api_reference.html#marshmallow.fields.Nested
    appointments = fields.Nested(AppointmentSchema, dump_only=True, many=True)

    @validates_schema
    def check_date_validation(self, data):
        if data['start_time'] >= data['end_time']:
            raise ValidationError('Start must be earlier than End')


class EventSchema(Schema):
    id = fields.Int(dump_only=True)  # read-only (won't be parsed by webargs)
    name = fields.Str(required=True)
    provider = fields.Nested(UserSchema, only=('email',), dump_only=True)  # read-only
    description = fields.Str(missing='')
    date_created = fields.DateTime(dump_only=True)  # read-only
    schedules = fields.Nested(ScheduleSchema, required=True, many=True)
