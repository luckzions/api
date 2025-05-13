from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4
import requests

app = FastAPI(title="Key Management API")

API_URL = "https://api-p2i6.onrender.com/"

def manter_api_viva():
    while True:
        try:
            print("👀 Pingando a API para manter ativa...")
            requests.get(API_URL)
        except Exception as e:
            print("Erro ao tentar manter a API viva:", e)
        time.sleep(600)  # a cada 10 minutos (600 segundos)

# Inicia o pinger em segundo plano
threading.Thread(target=manter_api_viva, daemon=True).start()

# Banco de dados em memória
keys_db = {}

class Key(BaseModel):
    key: str
    active: bool = True
    created_at: datetime
    validade_meses: int = 1
    numero: str = None

class VincularRequest(BaseModel):
    key: str
    numero: str

class VerifyRequest(BaseModel):
    key: str
    numero: str

def is_key_expired(key: Key) -> bool:
    validade = timedelta(days=key.validade_meses * 30)  # Aproximadamente 1 mês = 30 dias
    return datetime.utcnow() - key.created_at > validade

def generate_new_key() -> str:
    return str(uuid4())

@app.post("/vincular-key")
def vincular_key(data: VincularRequest):
    key = data.key
    numero = data.numero

    if not key or key not in keys_db:
        raise HTTPException(status_code=404, detail="Key not found")

    key_obj = keys_db[key]

    if not key_obj.active:
        raise HTTPException(status_code=403, detail="Key is inactive")

    if key_obj.numero and key_obj.numero != numero:
        raise HTTPException(status_code=403, detail="Key already in use by another number")

    key_obj.numero = numero
    return {"message": "Key vinculada com sucesso!", "numero": numero}

@app.post("/verify-key")
def verify_key(data: dict):
    key = data.get("key")

    if not key or key not in keys_db:
        raise HTTPException(status_code=403, detail="Invalid key")

    key_obj = keys_db[key]

    if is_key_expired(key_obj):
        key_obj.active = False

    dias_restantes = 0
    if key_obj.active:
        validade = timedelta(days=key_obj.validade_meses * 30)
        expiracao = key_obj.created_at + validade
        dias_restantes = (expiracao - datetime.utcnow()).days

    return {
        "key": key_obj.key,
        "numero": key_obj.numero,
        "ativa": key_obj.active,
        "criada_em": key_obj.created_at.isoformat(),
        "validade_meses": key_obj.validade_meses,
        "dias_restantes": dias_restantes
    }

@app.post("/keys", response_model=Key)
def create_key(validade_meses: int = 1):
    new_key = generate_new_key()
    key_obj = Key(key=new_key, created_at=datetime.utcnow(), validade_meses=validade_meses)
    keys_db[new_key] = key_obj
    return key_obj

@app.get("/keys", response_model=list[Key])
def list_keys():
    return list(keys_db.values())

@app.put("/keys/{key_id}/toggle", response_model=Key)
def toggle_key_status(key_id: str):
    if key_id not in keys_db:
        raise HTTPException(status_code=404, detail="Key not found")
    key = keys_db[key_id]
    key.active = not key.active
    return key

@app.delete("/keys/{key_id}")
def delete_key(key_id: str):
    if key_id not in keys_db:
        raise HTTPException(status_code=404, detail="Key not found")
    del keys_db[key_id]
    return {"detail": "Key deleted"}

@app.get("/")
def read_root():
    return {"message": "API online"}
