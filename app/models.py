from datetime import datetime, timedelta

import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, ma


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # https://docs.sqlalchemy.org/en/13/core/defaults.html#python-executed-functions
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)  # not utcnow()
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')  # bind `users` attribute to `Role`

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
            return 'Success'
        except jwt.ExpiredSignatureError:
            return 'Signature expired.'
        except jwt.InvalidTokenError:
            return 'Invalid token.'


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

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


# appointment - schedule 一对多
# a:
# .
# .
# .
# .
# .
class Event(db.Model):  # eg:  Office Hour / Meetings
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text())  # description by event provider
    # user - events 一对多
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    provider = db.relationship('User', backref='events')


class Schedule(db.Model):  # eg: 6月4日-8点到12点 / 6月5日-14点到18点
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # day = db.Column(db.Enum('',''), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime(), nullable=False)
    # event - schedules 一对多
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event = db.relationship('Event', backref='schedules')


class Appointment(db.Model):  # eg: 6月4日 8.30到9.30
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.Text())  # booker's message to provider
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime(), nullable=False)
    # schedule - appointments 一对多
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    schedule = db.relationship('Schedule', backref='appointments')
    # user - appointments 一对多
    booker_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    booker = db.relationship('User', backref='appointments')


# https://marshmallow-sqlalchemy.readthedocs.io/en/latest/index.html#generate-marshmallow-schemas
class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session


class RoleSchema(ma.ModelSchema):
    class Meta:
        model = Role
        sqla_session = db.session
