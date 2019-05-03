from flask_restful import Resource, reqparse, abort

from app.models import User

parser = reqparse.RequestParser()
parser.add_argument('email', required=True)
parser.add_argument('password', required=True)


class Registration(Resource):
    def post(self):
        # https://flask-restful.readthedocs.io/en/latest/quickstart.html#argument-parsing
        d = parser.parse_args(strict=True)

        if User.find_by_email(d['email']):
            abort(400, message="User {} already exists.".format(d['email']))

        new_user = User(email=d['email'], password=d['password'])

        try:
            new_user.save_to_db()
            # 坑 https://flask-restful.readthedocs.io/en/latest/extending.html#response-formats
            # flask_restful.Resource return (data, status code, headers)
            # flask.views return (response object, status code, headers)
            return {'message': 'Success.'}, 200
        except:
            return abort(500, message="Something went wrong.")
