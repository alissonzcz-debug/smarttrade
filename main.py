"""
SmartTrade Server - Railway.app
"""
import hashlib, os, time
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SECRET_KEY    = os.getenv("SECRET_KEY", "smarttrade_secret_2024")
EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

USERS = {
    "admin@smarttrade.com": hashlib.sha256("admin123".encode()).hexdigest(),
    "user1@smarttrade.com": hashlib.sha256("senha123".encode()).hexdigest(),
    "user2@smarttrade.com": hashlib.sha256("senha456".encode()).hexdigest(),
}

latest_data: dict = {
    "timestamp": time.time(),
    "cotacoes": {"indice": -0.0021, "dolar": -0.0019, "bancos": -0.0027, "acoes": 0.0033},
    "info_indice": {"direcao": "Sem Tend.", "exaustao": "Zona equil.", "correcao": "Continu.", "tendencia_primaria": "Baixa", "tendencia_secundaria": "Baixa"},
    "mercado": {"saldo_total": "Baixo", "volume": "Baixo"},
    "saldo_diario": {"inst": 4366, "pf": -5500},
    "saldo_5min": {"inst": 0, "pf": 0},
    "saldo_dolar": {"inst": -17092, "pf": 756},
    "top_vendidos": [{"nome": "003-XP", "valor": -7768}, {"nome": "127-Tullett", "valor": -5605}, {"nome": "039-Agora", "valor": -3971}, {"nome": "238-Goldman", "valor": -3970}, {"nome": "040-Morgan", "valor": -3446}],
    "top_comprados": [{"nome": "1618-Ideal", "valor": 8800}, {"nome": "120-Genial", "valor": 6796}, {"nome": "008-UBS", "valor": 5695}, {"nome": "092-Warren", "valor": 4235}, {"nome": "016-JP Morgan", "valor": 3441}],
    "top_vendidos_5min": [],
    "top_comprados_5min": [],
    "petr_vale": {"PETR3": -0.04, "PETR4": -0.41, "VALE3": 1.00},
    "top10_acoes": [{"ticker": "PETR4", "var": 1.2}, {"ticker": "VALE3", "var": 1.5}, {"ticker": "ITUB4", "var": 0.9}, {"ticker": "BBAS3", "var": 0.8}, {"ticker": "BBDC4", "var": -0.6}, {"ticker": "ELET3", "var": -1.0}, {"ticker": "B3SA3", "var": -0.4}, {"ticker": "ABEV3", "var": 0.3}, {"ticker": "WEGE3", "var": -1.3}, {"ticker": "PETR3", "var": 0.7}],
    "setor_financeiro": {"BBDC4": -0.5, "BBDC3": -0.9, "BPAC11": 0.3, "BPAN4": 0.2, "ITUB4": -0.4, "SANB11": 1.0, "BBAS3": -0.6},
    "acoes_ibov": [{"ticker": "RAIZ4", "var": 0.2}, {"ticker": "LWSA3", "var": -0.3}, {"ticker": "LREN3", "var": 0.5}],
    "termometro": {"pontos": 20, "maximo": 24}
}
active_sessions: Dict[str, str] = {}

def create_token(email: str) -> str:
    payload = {"email": email, "exp": datetime.utcnow() + timedelta(hours=12)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("email")
    except:
        return None

@app.post("/api/login")
async def login(body: dict):
    email = body.get("email", "").lower().strip()
    senha = body.get("senha", "")
    if email not in USERS:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    if USERS[email] != hashlib.sha256(senha.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    token = create_token(email)
    active_sessions[email] = token
    return {"token": token, "email": email}

@app.post("/api/dados")
async def receber_dados(body: dict):
    if body.get("api_key") != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    global latest_data
    novos_dados = body.get("dados", {})
    # Merge profundo
    for chave, valor in novos_dados.items():
        if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
            latest_data[chave].update(valor)
        else:
            latest_data[chave] = valor
    latest_data["timestamp"] = time.time()
    logger.info(f"✅ Dados atualizados via Excel")
    return {"ok": True}

@app.get("/api/poll")
async def poll(token: str = ""):
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    if active_sessions.get(email) != token:
        raise HTTPException(status_code=401, detail="Sessão encerrada")
    # Adiciona hora formatada
    dados = latest_data.copy()
    dados["hora"] = datetime.now().strftime("%H:%M:%S")
    return {"dados": dados}

@app.get("/api/status")
async def status():
    return {"online": True, "ultimo_dado": latest_data.get("timestamp")}

@app.get("/api/logout")
async def logout(token: str = ""):
    email = verify_token(token)
    if email and email in active_sessions:
        del active_sessions[email]
    return {"ok": True}

# Servir arquivos estáticos
if os.path.exists("client"):
    app.mount("/", StaticFiles(directory="client", html=True), name="static")

# Rota de fallback para SPA
@app.get("/{path:path}")
async def fallback(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    if os.path.exists(os.path.join("client", path)):
        return StaticFiles(directory="client").get_response(path)
    return StaticFiles(directory="client").get_response("index.html")
