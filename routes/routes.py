from flask import Flask, Blueprint
from flask_restplus import Api, Resource, fields

bp = Blueprint('bp', __name__)
app = Flask(__name__)
api = Api(app)
a_lang = api.model('Language', {'language' : fields.String('The language.')})

langs = []
python = {'language' : 'python', 'id' : 1}
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
        return {'result' : 'language added'}, 201

from app import *