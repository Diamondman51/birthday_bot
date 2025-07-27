from datetime import time
from pydantic import BaseModel

from models.models import Langs


class LangSchema(BaseModel):
    lang: Langs


class TimeSchema(BaseModel):
    time__: time
    