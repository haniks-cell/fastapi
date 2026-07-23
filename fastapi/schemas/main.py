from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent

class AddErrors(BaseModel):
    error_text: str
    endpont: str
    method: str
    # created_at: datetime
