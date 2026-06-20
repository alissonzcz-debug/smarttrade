import hashlib, os, time
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import jwt
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SECRET_KEY    = os.getenv("SECRET_KEY", "smarttrade_secret_2024")
EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

USERS = {
    "admin@smarttrade.com": hashlib.sha256("admin123".encode()).hexdigest(),
    "user1@smarttrade.com": hashlib.sha256("senha123".encode()).hexdigest(),
    "user2@smarttrade.com": hashlib.sha256("senha456".encode()).hexdigest(),
}

latest_data: dict = {}
active_sessions: Dict[str, str] = {}

def create_token(email):
    return jwt.encode({"email": email, "exp": datetime.utcnow() + timedelta(hours=12)}, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"]).get("email")
    except: return None

@app.post("/api/login")
async def login(body: dict):
    email = body.get("email","").lower().strip()
    senha = body.get("senha","")
    if email not in USERS or USERS[email] != hashlib.sha256(senha.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    token = create_token(email)
    active_sessions[email] = token
    return {"token": token, "email": email}

@app.post("/api/dados")
async def receber_dados(body: dict):
    if body.get("api_key") != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    global latest_data
    latest_data = body.get("dados", {})
    latest_data["timestamp"] = time.time()
    return {"ok": True}

@app.get("/api/poll")
async def poll(token: str = ""):
    email = verify_token(token)
    if not email: raise HTTPException(status_code=401, detail="Token inválido")
    if active_sessions.get(email) != token: raise HTTPException(status_code=401, detail="Sessão encerrada")
    return {"dados": latest_data}

@app.get("/api/status")
async def status():
    return {"online": True, "ultimo_dado": latest_data.get("timestamp")}

if os.path.exists("client"):
    app.mount("/", StaticFiles(directory="client", html=True), name="static")
