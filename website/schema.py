""" This file contains the schema for the token data. """
from pydantic import BaseModel

class TokenData(BaseModel):
    """ Token data schema. """
    user_id: int
    user_name: str
