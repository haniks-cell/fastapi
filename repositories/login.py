from datetime import timedelta, datetime, timezone

import jwt
import bcrypt
from schemas.login import setting



class LoginRepository:
    async def encode_jwt(
            self,
            payload: dict,
            key: str = setting.auth_jwt.private.read_text(),
            alhoritm: str = setting.auth_jwt.algorithm,
            expire_min: int = setting.auth_jwt.access_token_min,
            expire_timedelta: timedelta | None = None
                         ):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        to_enc = payload.copy()
        if expire_timedelta:
            expire = now + expire_timedelta
        else:
            expire = now + timedelta(minutes=expire_min)
        to_enc.update(exp=expire, iat=now)
        encoded = jwt.encode(to_enc, key, algorithm=alhoritm)
        return encoded
    async def decode_jwt(self,
            jwts: str,
            key: str = setting.auth_jwt.public.read_text(),
            alhoritm: str = setting.auth_jwt.algorithm):
        decoded = jwt.decode(jwts, key, algorithms=[alhoritm])
        return decoded
    
    async def hash_password(self,password:str) -> bytes:
        salt = bcrypt.gensalt()
        pwd_bytes: bytes = password.encode()
        return bcrypt.hashpw(pwd_bytes, salt)
    
    async def validate_password (self, password: str, hash_password: bytes) -> bool:
        return bcrypt.checkpw(password.encode(), hash_password)