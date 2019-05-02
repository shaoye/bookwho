from datetime import datetime
from . import db, ma


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # https://docs.sqlalchemy.org/en/13/core/defaults.html#python-executed-functions
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)  # not utcnow()
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')

    @staticmethod
    def insert_admin():
        pass


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
