from flask import current_app as app
from flask_restful import Resource, abort
from app.models import User, BlacklistToken
from marshmallow import fields, validate
from webargs.flaskparser import use_kwargs, parser

user_args = {
    'email': fields.Email(requried=True),
    'password': fields.Str(required=True)
}

token_args = {
    'auth_header': fields.Str(
        data_key='Authorization',
        location='headers',
        required=True,
        validate=validate.Regexp(r'^Bearer\s\S+')
    )
}


@use_kwargs(token_args)
def validate_token(auth_header):
    token = auth_header.split(' ')[1]

    if BlacklistToken.has_token(token):
        abort(400, status='fail', message='Revoked token.')

    result, payload = User.decode_token(token, app.config['SECRET_KEY'])
    if result != 'Success':
        abort(400, status='fail', message=result)

    return token, payload['sub']


class Registration(Resource):
    @use_kwargs(user_args)
    def post(self, email, password):
        if User.find_by_email(email):
            abort(400, message=f"User {email} already exists.")

        new_user = User(email=email, password=password)
        new_user.save_to_db()

        token = new_user.encode_token(app.config['SECRET_KEY'])

        response = {
            'status': 'success',
            'message': 'Successfully registered.',
            'auth_token': token
        }

        return response, 201
        # 坑 https://flask-restful.readthedocs.io/en/latest/extending.html#response-formats
        # flask_restful.Resource return (data, status code, headers)
        # flask.views return (response object, status code, headers)


class Login(Resource):
    @use_kwargs(user_args)
    def post(self, email, password):
        user = User.query.filter_by(email=email).first()

        if not user or not user.verify_password(password):
            abort(404, status='fail', message='Wrong email or password.')

        token = user.encode_token(app.config['SECRET_KEY'])

        response = {
            'status': 'success',
            'message': 'Successfully logged in',
            'auth_token': token
        }

        return response, 200


class Logout(Resource):
    def post(self):
        token, _ = validate_token()

        revoked_token = BlacklistToken(token=token)
        revoked_token.save_to_db()

        return {'status': 'success', 'message': 'Successfully logged out'}, 200


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err, req, schema, error_status_code, error_headers):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    abort(error_status_code, errors=err.messages)
