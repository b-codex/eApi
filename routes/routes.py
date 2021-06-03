import pyrebase
from datetime import timedelta
from flask import Flask, Blueprint
from flask_restplus import Api, Resource, fields
from flask_mobility import Mobility
from firebase_admin import credentials, firestore, initialize_app


firebaseConfig = {
    "apiKey": "AIzaSyDnN_lXnJRwcZrO3SBIbINjR20iJ5XhJyQ",
    "authDomain": "temaribet-af8a0.firebaseapp.com",
    "databaseURL": "https://temaribet-af8a0-default-rtdb.firebaseio.com",
    "projectId": "temaribet-af8a0",
    "storageBucket": "temaribet-af8a0.appspot.com",
    "messagingSenderId": "361477504348",
    "appId": "1:361477504348:web:bb1f559f4687130e691599"
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()
rdb = firebase.database()  # firebase realtime db only for storing users
strj = firebase.storage()
cred = credentials.Certificate(
    'temaribet-af8a0-firebase-adminsdk-w1moa-500c242ed6.json')
default_app = initialize_app(cred)

db = firestore.client()  # firebase firestore to store form related data


bp = Blueprint('bp', __name__)
app = Flask(__name__)
api = Api(app)

Mobility(app)
app.secret_key = "__temaribetsessionkey__"  # key for session
app.permanent_session_lifetime = timedelta(days=7)


a_lang = api.model('Language', {'language': fields.String('The language.')})

tutor_model = api.model('tutor', {
    'tutor_first_name': fields.String('tutor first name'),
    'tutor_last_name': fields.String('tutor last name'),
    'tutor_email': fields.String('tutor email'),
    'tutor_phone': fields.String('tutor phone'),
    'education_level': fields.String('education level'),
    'address': fields.String('address'),
    'sex': fields.String('sex')
})


langs = []
python = {'language': 'python', 'id': 1}
langs.append(python)


@api.route('/lang')
class Lang(Resource):

    @api.marshal_with(a_lang)
    def get(self):
        return langs

    @api.expect(a_lang)
    def post(self):
        new = api.payload
        new['id'] = len(langs) + 1
        langs.append(new)
        return {'result': 'language added'}, 201

@api.route('/tutor')
class tutor(Resource):
    def get(self):
        lenz = [t.to_dict() for t in list(db.collection('tutor_form').get())]
        return {'lenz': lenz}

    @api.expect(tutor_model)
    def post(self):
        lenz = len(list(db.collection('parent_form').get()))
        doc = {
            'id': lenz + 1,
            'assigned': False,
            'tutor_first_name': api.payload['tutor_first_name'],
            'tutor_last_name': api.payload['tutor_last_name'],
            'tutor_email': api.payload['tutor_email'],
            'tutor_phone': api.payload['tutor_phone'],
            'education_level': api.payload['education_level'],
            'address': api.payload['address'],
            'sex': api.payload['sex'],
        }
        db.collection('tutor_form').document(str(lenz + 1)).set(doc)
        return {
            'status': 201,
            'msg': 'Everything went perfect!, We will contact you using your email address.'
        }, 201

from app import *