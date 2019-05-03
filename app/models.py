from datetime import datetime

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


# https://marshmallow-sqlalchemy.readthedocs.io/en/latest/index.html#generate-marshmallow-schemas
class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session


class RoleSchema(ma.ModelSchema):
    class Meta:
        model = Role
        sqla_session = db.session
