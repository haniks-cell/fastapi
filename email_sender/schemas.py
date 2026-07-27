from pathlib import Path
from pydantic import BaseModel, EmailStr
from typing import Optional

class KafkaInput(BaseModel):
    email: EmailStr
    link: str

