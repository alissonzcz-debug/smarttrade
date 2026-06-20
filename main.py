import os
import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

# ============================================
# CONFIGURAÇÃO DE LOG
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# APP
# ============================================
app = FastAPI()

# ============================================
# CORS - PERMITIR TUDO
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# CONFIGURAÇÕES
# ============================================
EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

# ============================================
# DADOS PADRÃO (para funcionar mesmo sem dados)
# ============================================
DADOS_PADRAO = {
    "cotacoes": {
        "Índice Futuro": -0.21,
        "Dólar Futuro": -0.19,
        "Bancos": -0.27,
        "Ações IBOV": 0.33
    },
    "informacoes_indice": {
        "Direção": "Sem Tend.",
        "Exaustão": "Zona equil.",
        "Correção": "Continu.",
        "Tend. Primária": "Baixa",
        "Tend. Secundária": "Baixa"
    },
    "movimento_mercado": {
        "Saldo Total": "Baixo",
        "Volume": "Baixo"
    },
    "saldo_dolar": {
        "Institucional": -17092,
        "Varejo": 756
    },
    "saldo_diario": {
        "Institucional": 4366,
        "Varejo": -5500
    },
    "top_vendidos": [
        {"corretora": "003-XP", "qtd": -7768},
        {"corretora": "127-Tullett", "qtd": -5605},
        {"corretora": "039-Agora", "qtd": -3971},
        {"corretora": "238-Goldman", "qtd": -3970},
        {"corretora": "040-Morgan", "qtd": -3446}
    ],
    "top_comprados": [
        {"corretora": "1618-Ideal", "qtd": 8800},
        {"corretora": "120-Genial", "qtd": 6796},
        {"corretora": "008-UBS", "qtd": 5695},
        {"corretora": "092-Warren", "qtd": 4235},
        {"corretora": "016-JP Morgan", "qtd": 3441}
    ],
    "saldo_5min": {
        "Institucional": 0,
        "Varejo": 0
    },
    "petr_vale": {
        "PETR3": -0.04,
        "PETR4": -0.41,
        "VALE3": 1.00
    },
    "top_10_acoes": [
        {"ticker": "PETR4", "variacao": 1.2},
        {"ticker": "VALE3", "variacao": 1.5},
        {"ticker": "ITUB4", "variacao": 0.9},
        {"ticker": "BBAS3", "variacao": 0.8},
        {"ticker": "BBDC4", "variacao": -0.6},
        {"ticker": "ELET3", "variacao": -1.0},
        {"ticker": "B3SA3", "variacao": -0.4},
        {"ticker": "ABEV3", "variacao": 0.3},
        {"ticker": "WEGE3", "variacao": -1.3},
        {"ticker": "PETR3", "variacao": 0.7}
    ],
    "setor_financeiro": [
        {"ticker": "BBDC4", "variacao": -0.5},
        {"ticker": "BBDC3", "variacao": -0.9},
        {"ticker": "BPAC11", "variacao": 0.3},
        {"ticker": "BPAN4", "variacao": 0.2},
        {"ticker": "ITUB4", "variacao": -0.4},
        {"ticker": "SANB11", "variacao": 1.0},
        {"ticker": "BBAS3", "variacao": -0.6}
    ],
    "acoes_ibov": [
        "RAIZ4", "LWSA3", "LREN3", "CSNA3", "ENEV3", "VBBR3",
        "SLCE3", "MRVE3", "RAIL3", "ENGI11", "SBSP3", "IGTI11",
        "ALSO3", "WINT", "CPFE3", "TOTS4", "KLBN11", "PETR4",
        "BBDC3", "BBSE3", "ABEV3", "BRKM5", "CSAN3", "GGBR4",
        "GOAU4", "HAPV3", "HYPE3", "JBSS3", "JHSF3", "LEVE3",
        "MGLU3", "MOVI3", "MULT3", "PCAR3", "PETZ3", "QUAL3",
        "RADL3", "RDOR3", "RENT3", "SBFG3", "SOMA3", "SUZB3",
        "TAEE11", "TIMS3", "TOTS3", "UGPA3", "USIM5", "VALE3",
        "VIVT3", "YDUQ3"
    ]
}

# Estado em memória
latest_data: Dict[str, Any] = DADOS_PADRAO.copy()
latest_data["timestamp"] = time.time()

# ============================================
# MODELOS
# ============================================
class DadosRequest(BaseModel):
    api_key: str
    dados: Dict[str, Any]

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
@app.get("/index.html")
async def root():
    """Rota principal"""
    # Verifica se existe o frontend
    if os.path.exists("client/index.html"):
        # O StaticFiles vai servir
        return {"message": "Smart Trade API", "status": "online"}
    else:
        # Fallback
        return HTMLResponse("""
            <html>
                <head><title>Smart Trade</title></head>
                <body style="background:#0A0E17;color:#E8EDF5;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
                    <div style="text-align:center;">
                        <h1>📊 Smart Trade</h1>
                        <p style="color:#1DB954;">✅ API online!</p>
                        <p style="color:#5E7390;">Aguardando frontend...</p>
                        <br>
                        <a href="/api/status" style="color:#1DB954;">▶ Status</a>
                        <a href="/api/dados" style="color:#5E7390;margin-left:15px;">📊 Dados</a>
                    </div>
                </body>
            </html>
        """)

@app.post("/api/dados")
async def receber_dados(request: DadosRequest):
    """Recebe dados do Excel"""
    global latest_data
    
    # Verifica API key
    if request.api_key != EXCEL_API_KEY:
        logger.warning(f"API key inválida: {request.api_key[:10]}...")
        raise HTTPException(status_code=403, detail="API key inválida")
    
    try:
        novos_dados = request.dados
        
        # Atualiza os dados
        for chave, valor in novos_dados.items():
            if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
                latest_data[chave].update(valor)
            else:
                latest_data[chave] = valor
        
        latest_data["timestamp"] = time.time()
        
        logger.info(f"✅ Dados atualizados! Timestamp: {latest_data['timestamp']}")
        
        return {
            "ok": True,
            "timestamp": latest_data["timestamp"],
            "mensagem": "Dados recebidos com sucesso"
        }
    
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dados")
async def get_dados():
    """Retorna todos os dados"""
    return {"dados": latest_data}

@app.get("/api/dados/{categoria}")
async def get_categoria(categoria: str):
    """Retorna uma categoria específica"""
    if categoria not in latest_data:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return {categoria: latest_data[categoria]}

@app.get("/api/status")
async def status():
    """Status do servidor"""
    return {
        "online": True,
        "ultimo_dado": latest_data.get("timestamp"),
        "ultima_atualizacao": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(latest_data.get("timestamp", 0))),
        "categorias": list(latest_data.keys())
    }

@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

# ============================================
# SERVE ARQUIVOS ESTÁTICOS
# ============================================
if os.path.exists("client"):
    logger.info("📁 Servindo arquivos da pasta 'client'")
    app.mount("/", StaticFiles(directory="client", html=True), name="static")
else:
    logger.warning("⚠️ Pasta 'client' não encontrada")
