from flask import Flask
from api.v1.routes import auth, views


def create_app():
    app = Flask(__name__)
        
    app.register_blueprint(auth, url_prefix="/api/v1/auth")
    app.register_blueprint(views, url_prefix="/api/v1/views")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
