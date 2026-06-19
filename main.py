"""
SmartTrade Server - Railway.app
Recebe dados do Excel via POST e distribui para clientes via WebSocket
"""
import asyncio
import json
import hashlib
import os
import time
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import jwt
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CONFIGURAÇÕES ───────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "smarttrade_secret_2024")
EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

# Usuários (email → senha em hash SHA256)
# Para adicionar usuários: hash = hashlib.sha256("senha".encode()).hexdigest()
USERS = {
    "admin@smarttrade.com": hashlib.sha256("admin123".encode()).hexdigest(),
    "user1@smarttrade.com": hashlib.sha256("senha123".encode()).hexdigest(),
    "user2@smarttrade.com": hashlib.sha256("senha456".encode()).hexdigest(),
}

# ─── ESTADO ──────────────────────────────────────────────────
latest_data: dict = {}                          # últimos dados recebidos do Excel
active_sessions: Dict[str, str] = {}           # email → token ativo
connected_clients: Dict[str, WebSocket] = {}   # token → websocket

# ─── AUTH ────────────────────────────────────────────────────
def create_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("email")
    except:
        return None

# ─── ENDPOINTS HTTP ──────────────────────────────────────────

@app.post("/api/login")
async def login(body: dict):
    email = body.get("email", "").lower().strip()
    senha = body.get("senha", "")

    if email not in USERS:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    if USERS[email] != senha_hash:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    # Desconectar sessão anterior se existir
    token_antigo = active_sessions.get(email)
    if token_antigo and token_antigo in connected_clients:
        try:
            await connected_clients[token_antigo].send_json({"tipo": "kicked", "msg": "Nova sessão iniciada em outro dispositivo."})
            await connected_clients[token_antigo].close()
        except:
            pass
        del connected_clients[token_antigo]

    token = create_token(email)
    active_sessions[email] = token

    return {"token": token, "email": email}

@app.post("/api/dados")
async def receber_dados(body: dict):
    """Endpoint chamado pelo script Python no PC do trader"""
    api_key = body.get("api_key", "")
    if api_key != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")

    global latest_data
    latest_data = body.get("dados", {})
    latest_data["timestamp"] = time.time()

    # Enviar para todos os clientes conectados
    mortos = []
    for token, ws in connected_clients.items():
        try:
            await ws.send_json({"tipo": "dados", "dados": latest_data})
        except:
            mortos.append(token)

    for t in mortos:
        del connected_clients[t]

    return {"ok": True, "clientes": len(connected_clients)}

@app.get("/api/status")
async def status():
    return {
        "online": True,
        "clientes": len(connected_clients),
        "ultimo_dado": latest_data.get("timestamp", None)
    }

# ─── WEBSOCKET ───────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    email = verify_token(token)
    if not email:
        await websocket.close(code=4001)
        return

    # Verificar se o token é o ativo para esse email
    if active_sessions.get(email) != token:
        await websocket.close(code=4002)
        return

    await websocket.accept()
    connected_clients[token] = websocket

    # Enviar dados mais recentes imediatamente
    if latest_data:
        await websocket.send_json({"tipo": "dados", "dados": latest_data})

    try:
        while True:
            # Manter conexão viva com ping
            await asyncio.sleep(30)
            await websocket.send_json({"tipo": "ping"})
    except WebSocketDisconnect:
        if token in connected_clients:
            del connected_clients[token]

# ─── SERVIR SITE ESTÁTICO ────────────────────────────────────
if os.path.exists("client"):
    app.mount("/", StaticFiles(directory="client", html=True), name="static")
