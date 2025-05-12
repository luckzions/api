from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import Key, generate_new_key
from datetime import datetime
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timedelta
from collections import defaultdict

app = FastAPI(title="Key Management API")

# Banco de dados em memória
keys_db = {}

class Key(BaseModel):
    key: str
    active: bool = True
    created_at: datetime
    user_agent: str = None
    ip_address: str = None
    numero: str = None

class RegisterRequest(BaseModel):
    username: str
    password: str
    key: str

class VincularRequest(BaseModel):
    key: str
    numero: str

def generate_new_key() -> str:
    return str(uuid4())

def is_key_expired(key: Key) -> bool:
    expiration_time = timedelta(hours=1)  # A key expira após 1 hora
    return datetime.utcnow() - key.created_at > expiration_time

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

@app.get("/get-ip")
def get_ip(request: Request):
    ip_address = request.client.host  # Pega o IP do usuário
    return {"ip": ip_address}

@app.post("/verify-key")
def verify_key(payload: dict, request: Request):
    key = payload.get("key")
    
    if not key or key not in keys_db:
        raise HTTPException(status_code=403, detail="Invalid key")
    
    key_obj = keys_db[key]
    
    if not key_obj.active:
        raise HTTPException(status_code=403, detail="Key is inactive")
    
    if is_key_expired(key_obj):
        key_obj.active = False  # Desativa a key se expirou
        raise HTTPException(status_code=403, detail="Key has expired")
    
    # Coleta o IP e o User-Agent apenas na primeira vez que a key for utilizada
    if key_obj.user_agent is None or key_obj.ip_address is None:
        user_agent = request.headers.get("User-Agent")
        ip_address = request.client.host
        key_obj.user_agent = user_agent
        key_obj.ip_address = ip_address
    
    # Verifica se o IP e o User-Agent são válidos
    if key_obj.user_agent != request.headers.get("User-Agent") or key_obj.ip_address != request.client.host:
        raise HTTPException(status_code=403, detail="Invalid IP or User-Agent")
    
    return {"detail": "Key is valid"}

@app.post("/keys", response_model=Key)
def create_key():
    new_key = generate_new_key()
    key_obj = Key(key=new_key, created_at=datetime.utcnow())
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

# Serve static HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")