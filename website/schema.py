from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: str
    username: str
