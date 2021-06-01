from flask import Blueprint

second = Blueprint('second', __name__)

@second.route('/')
def home():
    return "home"