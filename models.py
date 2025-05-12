from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

class Key(BaseModel):
    key: str
    active: bool = True
    created_at: datetime
    numero: str = None

def generate_new_key() -> str:
    return str(uuid4())

def is_key_expired(key: Key) -> bool:
    expiration_time = timedelta(hours=1)  # A key expira após 1 hora
    return datetime.utcnow() - key.created_at > expiration_time

@app.get("/")
def read_root():
    return {"message": "API online"}