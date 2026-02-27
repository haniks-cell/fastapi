from pathlib import Path

from pydantic import BaseModel, Field, EmailStr
from pydantic_settings import BaseSettings

class TokenInfo(BaseModel):
    access_token: str
    token_type: str

class LoginCreate(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None
    active: bool = True

class JwtAuth(BaseModel):
    private: Path = "certs\private.pem"
    public: Path = 'certs\public.pem'
    algorithm: str = 'RS256'
    access_token_min: int = 3

class Setting(BaseSettings):
    auth_jwt: JwtAuth = JwtAuth()

setting = Setting()