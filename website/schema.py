from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: int
    user_name: str
