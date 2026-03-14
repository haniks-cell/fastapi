from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent

class TokenInfo(BaseModel):
    access_token: str
    token_type: str

class LoginCreate(BaseModel):
    username: str
    password: str
    lvl_access: int = 0
    email: EmailStr | None = None
    # active: bool = True

class JwtAuth(BaseModel):
    private: Path = BASE_DIR / "certs" /  "private.pem"
    public: Path = BASE_DIR / "certs" /  'public.pem'
    algorithm: str = 'RS256'
    access_token_min: int = 1

class TokenJwt(BaseModel):
    sub: int
    username: str
    email: str | None = None
    exp: int #health
    iat: int #create


class Setting(BaseSettings):
    auth_jwt: JwtAuth = JwtAuth()

setting = Setting()