import os
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
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
# CORS - PERMITIR TUDO (essencial para o Railway)
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

# Estado em memória (inicia com dados padrão)
latest_data: Dict[str, Any] = DADOS_PADRAO.copy()
latest_data["timestamp"] = time.time()
latest_data["ultima_atualizacao"] = time.strftime("%d/%m/%Y %H:%M:%S")

# ============================================
# MODELOS
# ============================================
class DadosRequest(BaseModel):
    api_key: str
    dados: Dict[str, Any]

# ============================================
# ENDPOINTS DA API
# ============================================

@app.get("/")
async def root():
    """Rota principal - serve o frontend se existir"""
    # Tenta servir o index.html da pasta client
    if os.path.exists("client/index.html"):
        return FileResponse("client/index.html")
    else:
        # Fallback: mostra status da API
        return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Smart Trade API</title>
                <style>
                    body { background: #0A0E17; color: #E8EDF5; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                    .container { text-align: center; max-width: 600px; padding: 40px; }
                    h1 { color: #1DB954; font-size: 32px; }
                    .status { color: #5E7390; font-size: 14px; margin: 20px 0; }
                    .endpoints { text-align: left; background: #111827; padding: 20px; border-radius: 8px; border: 1px solid #1E2A3A; }
                    .endpoints code { color: #1DB954; }
                    .missing { color: #F4A020; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Smart Trade</h1>
                    <div class="status">✅ API está online!</div>
                    <div class="endpoints">
                        <div><code>GET /api/dados</code> - Ver todos os dados</div>
                        <div><code>GET /api/status</code> - Status do servidor</div>
                        <div><code>GET /api/health</code> - Health check</div>
                        <div><code>POST /api/dados</code> - Enviar dados (requer API Key)</div>
                    </div>
                    <div class="missing">
                        ⚠️ Frontend não encontrado. Crie uma pasta <code>client/</code> com <code>index.html</code>
                    </div>
                </div>
            </body>
            </html>
        """)

@app.post("/api/dados")
async def receber_dados(request: DadosRequest):
    """Recebe dados do Excel/planilha"""
    global latest_data
    
    # Verifica API key
    if request.api_key != EXCEL_API_KEY:
        logger.warning(f"❌ API key inválida: {request.api_key[:10]}...")
        raise HTTPException(status_code=403, detail="API key inválida")
    
    try:
        novos_dados = request.dados
        
        # Atualiza os dados (merge profundo)
        for chave, valor in novos_dados.items():
            if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
                latest_data[chave].update(valor)
            else:
                latest_data[chave] = valor
        
        # Atualiza timestamp
        latest_data["timestamp"] = time.time()
        latest_data["ultima_atualizacao"] = time.strftime("%d/%m/%Y %H:%M:%S")
        
        logger.info(f"✅ Dados atualizados! Timestamp: {latest_data['timestamp']}")
        
        return {
            "ok": True,
            "timestamp": latest_data["timestamp"],
            "ultima_atualizacao": latest_data["ultima_atualizacao"],
            "mensagem": "Dados recebidos com sucesso"
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao processar dados: {str(e)}")
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
    """Status do servidor"""
    return {
        "online": True,
        "ultimo_dado": latest_data.get("timestamp"),
        "ultima_atualizacao": latest_data.get("ultima_atualizacao", "Nunca"),
        "total_categorias": len([k for k in latest_data.keys() if k not in ["timestamp", "ultima_atualizacao"]]),
        "categorias": [k for k in latest_data.keys() if k not in ["timestamp", "ultima_atualizacao"]]
    }

@app.get("/api/health")
async def health():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "uptime": time.strftime("%d/%m/%Y %H:%M:%S")
    }

# ============================================
# SERVE ARQUIVOS ESTÁTICOS (CSS, JS, imagens)
# ============================================

# Verifica se existe a pasta 'client'
if os.path.exists("client"):
    logger.info("📁 Servindo arquivos estáticos da pasta 'client'")
    
    # Monta a pasta client para arquivos estáticos (CSS, JS, imagens)
    app.mount("/static", StaticFiles(directory="client"), name="static")
    
    # Rota para servir o index.html diretamente
    @app.get("/index.html")
    async def serve_index_html():
        if os.path.exists("client/index.html"):
            return FileResponse("client/index.html")
        return HTMLResponse("<h1>index.html não encontrado</h1>", status_code=404)
    
    # Rota para servir qualquer arquivo da pasta client
    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = os.path.join("client", path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Se não encontrar o arquivo, tenta servir o index.html (SPA fallback)
        if os.path.exists("client/index.html"):
            return FileResponse("client/index.html")
        return HTMLResponse(f"Arquivo não encontrado: {path}", status_code=404)

else:
    logger.warning("⚠️ Pasta 'client' não encontrada")
    
    @app.get("/{path:path}")
    async def serve_not_found(path: str):
        return HTMLResponse(f"""
            <html>
                <head><title>Smart Trade</title></head>
                <body style="background:#0A0E17;color:#E8EDF5;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
                    <div style="text-align:center;">
                        <h1>📊 Smart Trade</h1>
                        <p style="color:#1DB954;">✅ API online!</p>
                        <p style="color:#5E7390;">Pasta <code>client/</code> não encontrada.</p>
                        <br>
                        <a href="/api/status" style="color:#1DB954;">▶ Status</a>
                        <a href="/api/dados" style="color:#5E7390;margin-left:15px;">📊 Dados</a>
                    </div>
                </body>
            </html>
        """)

# ============================================
# HANDLER DE ERROS
# ============================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"erro": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"erro": "Erro interno do servidor"}
    )

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 SMART TRADE API")
    print("="*60)
    print(f"📊 API Key: {EXCEL_API_KEY}")
    print(f"📁 Pasta client: {'✅ Existe' if os.path.exists('client') else '❌ Não existe'}")
    print(f"📄 index.html: {'✅ Encontrado' if os.path.exists('client/index.html') else '❌ Não encontrado'}")
    print("="*60)
    print("🌐 Acesse: http://localhost:8000")
    print("📡 API Docs: http://localhost:8000/docs")
    print("📊 Status: http://localhost:8000/api/status")
    print("="*60 + "\n")
    
    # Porta padrão para Railway é 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
