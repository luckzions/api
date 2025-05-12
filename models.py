from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

class Key(BaseModel):
    key: str
    active: bool = True
    created_at: datetime
    validade_meses: int = 1
    numero: str = None

def generate_new_key() -> str:
    return str(uuid4())

def is_key_expired(key: Key) -> bool:
    validade = timedelta(days=key.validade_meses * 30)  # Aproximadamente 1 mês = 30 dias
    return datetime.utcnow() - key.created_at > validade
