import os, time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

latest_data: dict = {}

# ── CONTADOR DE ONLINE ────────────────────────────────────────────────────
# Guarda timestamp da última chamada por IP
online_sessions: dict = {}
ONLINE_TIMEOUT = 15  # segundos sem ping = offline

@app.post("/api/dados")
async def receber_dados(body: dict):
    if body.get("api_key") != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    global latest_data
    latest_data = body.get("dados", {})
    latest_data["timestamp"] = time.time()
    return {"ok": True}

@app.get("/api/dados")
async def get_dados():
    return {"dados": latest_data}

@app.post("/api/online")
async def online_ping(request: Request):
    """Cada cliente faz POST a cada 5s. Retorna quantos estão ativos."""
    ip = request.client.host
    now = time.time()
    online_sessions[ip] = now
    # Remove sessões inativas
    ativos = {k: v for k, v in online_sessions.items() if now - v < ONLINE_TIMEOUT}
    online_sessions.clear()
    online_sessions.update(ativos)
    return {"online": len(online_sessions)}

@app.get("/api/status")
async def status():
    return {"online": True, "ultimo_dado": latest_data.get("timestamp")}

if os.path.exists("client"):
    app.mount("/", StaticFiles(directory="client", html=True), name="static")
