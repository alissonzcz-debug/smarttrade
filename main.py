import os
import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

# ============================================
# LOGGING (para debug)
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# APP
# ============================================
app = FastAPI(
    title="Smart Trade API",
    description="API para dados do Smart Trade - Mini Índice",
    version="1.0.0"
)

# ============================================
# CORS (permitir acesso de qualquer lugar)
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================
# CONFIGURAÇÕES
# ============================================
EXCEL_API_KEY = os.getenv("EXCEL_API_KEY", "minha_chave_excel_123")

# ============================================
# DADOS PADRÃO (iniciais)
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

# Estado em memória (inicia com dados padrão)
latest_data: Dict[str, Any] = DADOS_PADRAO.copy()
latest_data["timestamp"] = time.time()

# ============================================
# MODELOS DE DADOS (validação)
# ============================================
class DadosRequest(BaseModel):
    api_key: str
    dados: Dict[str, Any]

class DadosResponse(BaseModel):
    dados: Dict[str, Any]
    timestamp: float

# ============================================
# ENDPOINTS DA API
# ============================================

@app.get("/")
@app.get("/index.html")
async def root():
    """Rota raiz - redireciona para o frontend ou mostra status"""
    return {
        "message": "Smart Trade API está online!",
        "status": "running",
        "endpoints": {
            "GET /api/dados": "Retorna todos os dados",
            "POST /api/dados": "Envia novos dados (requer api_key)",
            "GET /api/status": "Status do servidor",
            "GET /api/health": "Health check"
        }
    }

@app.post("/api/dados")
async def receber_dados(request: DadosRequest):
    """Recebe dados atualizados do Excel/planilha"""
    global latest_data
    
    # Verifica a API key
    if request.api_key != EXCEL_API_KEY:
        logger.warning(f"Tentativa de acesso com API key inválida: {request.api_key[:5]}...")
        raise HTTPException(status_code=403, detail="API key inválida")
    
    try:
        novos_dados = request.dados
        
        # Atualiza os dados (merge profundo)
        for chave, valor in novos_dados.items():
            if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
                # Merge de dicionários aninhados
                latest_data[chave].update(valor)
            else:
                latest_data[chave] = valor
        
        # Atualiza timestamp
        latest_data["timestamp"] = time.time()
        
        logger.info(f"Dados atualizados com sucesso! Timestamp: {latest_data['timestamp']}")
        
        return {
            "ok": True,
            "timestamp": latest_data["timestamp"],
            "mensagem": "Dados atualizados com sucesso"
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar dados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")

@app.get("/api/dados")
async def get_dados():
    """Retorna todos os dados atuais"""
    return {"dados": latest_data}

@app.get("/api/dados/{categoria}")
async def get_categoria(categoria: str):
    """Retorna uma categoria específica dos dados"""
    if categoria not in latest_data:
        raise HTTPException(status_code=404, detail=f"Categoria '{categoria}' não encontrada")
    return {categoria: latest_data[categoria]}

@app.get("/api/status")
async def status():
    """Verifica o status da API"""
    timestamp = latest_data.get("timestamp", 0)
    return {
        "online": True,
        "ultimo_dado": timestamp,
        "ultima_atualizacao": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(timestamp)),
        "total_categorias": len([k for k in latest_data.keys() if k != "timestamp"])
    }

@app.get("/api/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/api/exemplo")
async def get_exemplo():
    """Retorna dados de exemplo para testar o frontend"""
    return {
        "dados": {
            "cotacoes": {
                "Índice Futuro": -0.15,
                "Dólar Futuro": -0.10
            },
            "top_10_acoes": [
                {"ticker": "PETR4", "variacao": 2.5},
                {"ticker": "VALE3", "variacao": 1.8}
            ]
        }
    }

# ============================================
# SERVE ARQUIVOS ESTÁTICOS (Frontend)
# ============================================

# Verifica se existe a pasta 'client' com os arquivos do frontend
CLIENT_DIR = "client"
if os.path.exists(CLIENT_DIR):
    # Verifica se o index.html existe
    index_path = os.path.join(CLIENT_DIR, "index.html")
    if os.path.exists(index_path):
        logger.info(f"📁 Servindo arquivos estáticos da pasta: {CLIENT_DIR}")
        app.mount("/", StaticFiles(directory=CLIENT_DIR, html=True), name="static")
    else:
        logger.warning(f"⚠️ Pasta '{CLIENT_DIR}' existe, mas não tem index.html")
        
        @app.get("/")
        async def serve_index_fallback():
            return HTMLResponse("""
                <html>
                    <head><title>Smart Trade</title></head>
                    <body style="background:#0A0E17;color:#E8EDF5;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;">
                        <div style="text-align:center;">
                            <h1>📊 Smart Trade</h1>
                            <p style="color:#5E7390;">API está online, mas o frontend não foi encontrado.</p>
                            <p style="color:#5E7390;font-size:12px;">Crie um arquivo <code>client/index.html</code></p>
                            <br>
                            <a href="/api/status" style="color:#1DB954;">▶ Status da API</a>
                        </div>
                    </body>
                </html>
            """)
else:
    # Se não existir a pasta client, mostra uma mensagem
    logger.warning("⚠️ Pasta 'client' não encontrada. Criando rotas de fallback...")
    
    @app.get("/")
    async def serve_no_client():
        return HTMLResponse("""
            <html>
                <head><title>Smart Trade - API</title></head>
                <body style="background:#0A0E17;color:#E8EDF5;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;">
                    <div style="text-align:center;max-width:500px;">
                        <h1>🚀 Smart Trade API</h1>
                        <p style="color:#1DB954;">✅ API está online!</p>
                        <p style="color:#5E7390;font-size:14px;">Para visualizar o dashboard:</p>
                        <ol style="text-align:left;color:#5E7390;font-size:12px;margin:20px auto;max-width:300px;">
                            <li>Crie uma pasta <code>client/</code></li>
                            <li>Coloque o <code>index.html</code> dentro</li>
                            <li>Recarregue a página</li>
                        </ol>
                        <br>
                        <a href="/api/status" style="color:#1DB954;text-decoration:none;border:1px solid #1DB954;padding:8px 20px;border-radius:4px;">▶ Status da API</a>
                        <a href="/api/dados" style="color:#5E7390;text-decoration:none;border:1px solid #5E7390;padding:8px 20px;border-radius:4px;margin-left:10px;">📊 Ver Dados</a>
                    </div>
                </body>
            </html>
        """)

# ============================================
# HANDLER DE ERROS GLOBAIS
# ============================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"erro": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"erro": "Erro interno do servidor", "detalhe": str(exc) if os.getenv("DEBUG") else None}
    )

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*50)
    print("🚀 SMART TRADE API")
    print("="*50)
    print(f"📊 API Key: {EXCEL_API_KEY}")
    print(f"📁 Pasta client: {'✅ Existe' if os.path.exists('client') else '❌ Não existe'}")
    print(f"📄 index.html: {'✅ Encontrado' if os.path.exists('client/index.html') else '❌ Não encontrado'}")
    print("="*50)
    print("🌐 Acesse: http://localhost:8000")
    print("📡 API Docs: http://localhost:8000/docs")
    print("📊 Status: http://localhost:8000/api/status")
    print("="*50 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
