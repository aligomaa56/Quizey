from flask import Blueprint, request, jsonify

views = Blueprint('views', __name__)

@views.route('/')
def index():
    return jsonify({'message': 'Hello, World!'})
