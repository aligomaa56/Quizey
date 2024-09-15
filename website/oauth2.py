""" OAuth2 functions """
from flask import request, jsonify
from datetime import datetime, timedelta
from database import get_db
from models import User
import jwt
from config import settings
from schema import TokenData

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    """ Create an access token.
    Args:
        data (dict): The data to encode in the token.
    Returns:
        str: The encoded access token.
"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    """ Verify an access token.
    Args:
        token (str): The access token to verify.
    Returns:
        TokenData: The token data if the token is valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        user_name = payload.get("user_name")
        if not user_id or not user_name:
            return None
        token_data = TokenData(user_id=user_id, user_name=user_name)
        return token_data
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(token: str, db=get_db()):
    """ Get the current user.
    Args:
        token (str): The access token.
        db (Session): The database session.
    Returns:
        User: The current user if the token is valid, otherwise None.
        """
    token_data = verify_access_token(token)
    if not token_data:
        return None
    user = db.query(User).filter(User.id == token_data.user_id, User.username == token_data.user_name).first()
    if not user:
        return None
    return user