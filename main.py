import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

# ============================================
# DADOS PADRÃO
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

latest_data: Dict[str, Any] = DADOS_PADRAO.copy()
latest_data["timestamp"] = time.time()

class DadosRequest(BaseModel):
    api_key: str
    dados: Dict[str, Any]

# ============================================
# ENDPOINTS
# ============================================

@app.post("/api/dados")
async def receber_dados(request: DadosRequest):
    global latest_data
    if request.api_key != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    
    for chave, valor in request.dados.items():
        if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
            latest_data[chave].update(valor)
        else:
            latest_data[chave] = valor
    
    latest_data["timestamp"] = time.time()
    logger.info(f"✅ Dados atualizados!")
    return {"ok": True, "timestamp": latest_data["timestamp"]}

@app.get("/api/dados")
async def get_dados():
    return {"dados": latest_data}

@app.get("/api/status")
async def status():
    return {
        "online": True,
        "ultimo_dado": latest_data.get("timestamp"),
        "ultima_atualizacao": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(latest_data.get("timestamp", 0)))
    }

# ============================================
# PÁGINA PRINCIPAL - HTML DE TESTE
# ============================================
@app.get("/")
async def index():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Trade - TESTE</title>
        <style>
            body {
                background: #0A0E17;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: Arial, sans-serif;
            }
            .box {
                background: #1DB954;
                color: #0A0E17;
                padding: 50px 70px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 0 60px rgba(29, 185, 84, 0.4);
            }
            .box h1 {
                font-size: 52px;
                margin: 0;
            }
            .box p {
                font-size: 18px;
                margin: 10px 0 0 0;
                opacity: 0.8;
            }
            .info {
                margin-top: 30px;
                color: #5E7390;
                font-size: 14px;
            }
            .info a {
                color: #1DB954;
                text-decoration: none;
            }
            .info a:hover {
                text-decoration: underline;
            }
            .badge {
                display: inline-block;
                background: #0A0E17;
                color: #1DB954;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div>
            <div class="box">
                <h1>✅ FUNCIONOU!</h1>
                <p>O servidor está online e servindo esta página</p>
                <div class="badge">🚀 TESTE BEM-SUCEDIDO</div>
            </div>
            <div class="info">
                <p>📡 <a href="/api/status" target="_blank">Status da API</a> &nbsp;|&nbsp; 📊 <a href="/api/dados" target="_blank">Ver Dados</a></p>
                <p style="font-size:12px;margin-top:8px;" id="hora"></p>
            </div>
        </div>
        <script>
            document.getElementById('hora').textContent = '🕐 ' + new Date().toLocaleString('pt-BR');
        </script>
    </body>
    </html>
    """)

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("\n" + "="*50)
    print("🚀 SMART TRADE - TESTE")
    print("="*50)
    print(f"🌐 Acesse: http://localhost:{port}")
    print(f"📊 Status: http://localhost:{port}/api/status")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
