from flask import Blueprint
"""
This module initializes the Flask Blueprints for the API routes.

Blueprints:
    auth (Blueprint): Blueprint for authentication-related routes.
    views (Blueprint): Blueprint for view-related routes.

Imports:
    from api.v1.routes.auth import *: Imports all routes from the auth module.
    from api.v1.routes.analytics import *: Imports all routes from the analytics module.
    from api.v1.routes.answer import *: Imports all routes from the answer module.
    from api.v1.routes.bank import *: Imports all routes from the bank module.
    from api.v1.routes.question_bank import *: Imports all routes from the question_bank module.
    from api.v1.routes.question import *: Imports all routes from the question module.
    from api.v1.routes.user import *: Imports all routes from the user module.
    from api.v1.routes.quiz_attempt import *: Imports all routes from the quiz_attempt module.
    from api.v1.routes.quiz import *: Imports all routes from the quiz module.
"""

auth = Blueprint('auth', __name__)
views = Blueprint('views', __name__)

from api.v1.routes.auth import *
from api.v1.routes.analytics import *
from api.v1.routes.answer import *
from api.v1.routes.bank import *
from api.v1.routes.question_bank import *
from api.v1.routes.question import *
from api.v1.routes.user import *
from api.v1.routes.quiz_attempt import *
from api.v1.routes.quiz import *
