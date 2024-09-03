from flask import Flask, request, session, jsonify
from auth import auth
from views import views

def create_app():
    app = Flask(__name__)
        
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(views, url_prefix="/views")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
