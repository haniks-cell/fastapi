from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).parent.parent

class confirmEmail(BaseModel):
    token: str

class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str= 'Bearer'

class ResponseServiceLogin (BaseModel):
    # tid: int
    token: str
    refresh: str

class LoginCreateInp(BaseModel):
    username: str
    hash_password: str
    email: Optional[EmailStr] = None
    # active: bool = True

class LoginCreate (LoginCreateInp):
    lvl_access: int = 0
    # email:EmailStr

class LoginCreateResponse(BaseModel):
    ok: bool

class LoginGet (BaseModel):
    username: str
    hash_password: str
# class Check (BaseModel):
#     ok: bool

class Login (LoginCreate):
    hash_password: bytes
    tid: int

class RefreshTokensCreate(BaseModel):
    user_id: int
    uuid: str

class JwtAuth(BaseModel):
    private: Path = BASE_DIR / "certs" /  "private.pem"
    public: Path = BASE_DIR / "certs" /  'public.pem'
    algorithm: str = 'RS256'
    access_token_min: int = 15
    refresh_token_days: int = 30

class TokenJwt(BaseModel):
    sub: int
    username: str
    lvl_access: int = 0
    exp: int #health
    iat: int #create

class TOTPCreateResponse(BaseModel):
    uri: str

class Setting(BaseSettings):
    auth_jwt: JwtAuth = JwtAuth()


setting = Setting()


class GoogleIdTokenPayload(BaseModel):
    iss: str
    azp: str
    aud: str
    sub: str
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = None
    at_hash: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    locale: Optional[str] = None
    iat: int
    exp: int
 
    
class GoogleOAUTHResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    token_type: str
    id_token: GoogleIdTokenPayload
    refresh_token_expires_in: Optional[int] = None