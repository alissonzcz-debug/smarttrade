import os
import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="Smart Trade API", version="1.0")

# CORS - permite qualquer origem (útil para desenvolvimento)
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

# Dados em memória (simulando um banco)
latest_data: Dict[str, Any] = {
    "cotacoes": {
        "indice_futuro": -0.21,
        "dolar_futuro": -0.19,
        "bancos": -0.27,
        "acoes_ibov": 0.33
    },
    "informacoes_indice": {
        "direcao": "Sem Tend.",
        "exaustao": "Zona equil.",
        "correcao": "Continu.",
        "tend_primaria": "Baixa",
        "tend_secundaria": "Baixa"
    },
    "movimento_mercado": {
        "saldo_total": "Baixo",
        "volume": "Baixo"
    },
    "saldo_dolar": {
        "institucional": -17092,
        "varejo": 756
    },
    "saldo_diario": {
        "institucional": 4366,
        "varejo": -5500
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
        "institucional": 0,
        "varejo": 0
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
    ],
    "timestamp": time.time()
}

# ============================================
# MODELOS DE DADOS (validação)
# ============================================
class DadosRequest(BaseModel):
    api_key: str
    dados: Dict[str, Any]

# ============================================
# ENDPOINTS DA API
# ============================================

@app.post("/api/dados")
async def receber_dados(request: DadosRequest):
    """Recebe dados atualizados do Excel/planilha"""
    if request.api_key != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    
    global latest_data
    
    # Atualiza mantendo a estrutura existente
    novos_dados = request.dados
    for chave, valor in novos_dados.items():
        if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
            # Merge de dicionários aninhados
            latest_data[chave].update(valor)
        else:
            latest_data[chave] = valor
    
    latest_data["timestamp"] = time.time()
    return {"ok": True, "timestamp": latest_data["timestamp"]}

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
    """Verifica se a API está online"""
    return {
        "online": True,
        "ultimo_dado": latest_data.get("timestamp"),
        "ultima_atualizacao": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(latest_data.get("timestamp", 0)))
    }

@app.get("/api/health")
async def health_check():
    """Health check para monitoramento"""
    return {"status": "healthy", "version": "1.0"}

# ============================================
# SERVE ARQUIVOS ESTÁTICOS (Frontend)
# ============================================

# Verifica se existe a pasta 'client' com os arquivos do frontend
if os.path.exists("client"):
    # Monta a pasta client como raiz para arquivos estáticos
    app.mount("/", StaticFiles(directory="client", html=True), name="static")
else:
    # Se não existir, cria uma rota para servir o HTML diretamente
    @app.get("/")
    async def serve_index():
        # Você pode colocar o HTML inline aqui ou retornar um arquivo
        return {"message": "Frontend não encontrado. Crie uma pasta 'client' com o arquivo index.html"}

# ============================================
# ROTA PARA DADOS EXEMPLO (útil para testes)
# ============================================
@app.get("/api/exemplo")
async def get_exemplo():
    """Retorna dados de exemplo para testar o frontend"""
    return {
        "dados": {
            "cotacoes": {
                "indice_futuro": -0.21,
                "dolar_futuro": -0.19,
                "bancos": -0.27,
                "acoes_ibov": 0.33
            },
            "top_10_acoes": [
                {"ticker": "PETR4", "variacao": 1.2},
                {"ticker": "VALE3", "variacao": 1.5},
                {"ticker": "ITUB4", "variacao": 0.9}
            ]
        }
    }

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Smart Trade API iniciando...")
    print(f"📊 API Key: {EXCEL_API_KEY}")
    print(f"🌐 Acesse: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
