from flask import Blueprint

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