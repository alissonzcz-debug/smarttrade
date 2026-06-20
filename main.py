import os
import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

# ============================================
# CONFIGURAÇÃO
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
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
# ENDPOINTS DA API
# ============================================

@app.post("/api/dados")
async def receber_dados(request: DadosRequest):
    global latest_data
    if request.api_key != EXCEL_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida")
    
    try:
        for chave, valor in request.dados.items():
            if chave in latest_data and isinstance(latest_data[chave], dict) and isinstance(valor, dict):
                latest_data[chave].update(valor)
            else:
                latest_data[chave] = valor
        
        latest_data["timestamp"] = time.time()
        logger.info(f"✅ Dados atualizados! Timestamp: {latest_data['timestamp']}")
        return {"ok": True, "timestamp": latest_data["timestamp"]}
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# ============================================
# HTML COMPLETO (gerado pelo servidor)
# ============================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Trade — Mini Índice</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0A0E17; display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: 'Segoe UI', 'Calibri', sans-serif; padding: 20px; }
        .container { background: #0F1521; border-radius: 12px; border: 1px solid #1E2A3A; max-width: 1200px; width: 100%; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.6); }
        .topbar { background: #111827; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1E2A3A; flex-wrap: wrap; gap: 8px; }
        .topbar-left { display: flex; align-items: center; gap: 10px; }
        .live-dot { width: 8px; height: 8px; background: #1DB954; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        .topbar-title { color: #E8EDF5; font-size: 13px; font-weight: 700; letter-spacing: 0.05em; }
        .topbar-title span { color: #5E7390; font-weight: 400; }
        .topbar-right { display: flex; align-items: center; gap: 12px; }
        .topbar-status { font-size: 10px; padding: 2px 10px; border-radius: 10px; background: #1A2538; color: #1DB954; }
        .topbar-time { color: #5E7390; font-size: 11px; }

        .main-grid { display: grid; grid-template-columns: 220px 1fr 280px; gap: 6px; padding: 6px; }
        .card { background: #111827; border: 1px solid #1E2A3A; border-radius: 6px; padding: 10px 12px; }
        .card-title { color: #5E7390; font-size: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid #1A2538; padding-bottom: 5px; margin-bottom: 6px; }
        .card-title.green { color: #1DB954; }
        .card-title.red { color: #E63946; }
        .card-title.yellow { color: #F4A020; }
        .row-item { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #1A2538; font-size: 10px; }
        .row-item:last-child { border-bottom: none; }
        .row-label { color: #5E7390; }
        .row-value { font-weight: 700; }
        .row-value.pos { color: #1DB954; }
        .row-value.neg { color: #E63946; }
        .row-value.neu { color: #F4A020; }
        .row-value.gray { color: #5E7390; }

        .bar-wrap { margin: 4px 0; }
        .bar-label { display: flex; justify-content: space-between; font-size: 9px; color: #5E7390; margin-bottom: 2px; }
        .bar-label .val { font-weight: 700; }
        .bar-label .val.pos { color: #1DB954; }
        .bar-label .val.neg { color: #E63946; }
        .bar-track { background: #1A2538; border-radius: 2px; height: 8px; position: relative; overflow: hidden; }
        .bar-fill { position: absolute; top: 0; height: 100%; border-radius: 2px; }
        .bar-fill.green { background: #1DB954; }
        .bar-fill.red { background: #E63946; }

        .table-mini { width: 100%; border-collapse: collapse; font-size: 10px; }
        .table-mini th { color: #5E7390; font-weight: 400; text-transform: uppercase; font-size: 7px; text-align: left; padding: 2px 0; border-bottom: 1px solid #1A2538; }
        .table-mini th:last-child { text-align: right; }
        .table-mini td { padding: 3px 0; border-bottom: 1px solid #1A2538; }
        .table-mini td:last-child { text-align: right; font-weight: 700; }
        .table-mini tr:last-child td { border-bottom: none; }
        .table-mini .pos { color: #1DB954; }
        .table-mini .neg { color: #E63946; }

        .duo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
        .pv-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px; }
        .pv-item { text-align: center; background: #1A2538; border-radius: 4px; padding: 6px 2px; }
        .pv-item .ticker { font-size: 7px; color: #5E7390; text-transform: uppercase; }
        .pv-item .change { font-size: 12px; font-weight: 700; }
        .pv-item .change.pos { color: #1DB954; }
        .pv-item .change.neg { color: #E63946; }

        .progress-item { display: flex; align-items: center; gap: 4px; padding: 2px 0; border-bottom: 1px solid #1A2538; font-size: 9px; }
        .progress-item:last-child { border-bottom: none; }
        .progress-label { color: #5E7390; width: 35px; flex-shrink: 0; font-size: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .progress-track { flex: 1; height: 5px; background: #1A2538; border-radius: 2px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 2px; }
        .progress-fill.green { background: #1DB954; }
        .progress-fill.red { background: #E63946; }
        .progress-pct { width: 32px; text-align: right; font-weight: 700; font-size: 8px; flex-shrink: 0; }
        .progress-pct.pos { color: #1DB954; }
        .progress-pct.neg { color: #E63946; }

        .ibov-container { overflow-x: auto; padding: 4px 0; }
        .ibov-wrap { display: flex; align-items: flex-end; height: 60px; gap: 2px; min-width: 100%; }
        .ibov-col { display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 12px; }
        .ibov-bar { width: 100%; border-radius: 1px; min-height: 1px; }
        .ibov-label { font-size: 5px; color: #5E7390; transform: rotate(-90deg); white-space: nowrap; margin-top: 3px; width: 24px; text-align: right; }

        .thermo-wrap { display: flex; justify-content: center; padding: 4px 0; }
        .col-left { grid-column: 1; grid-row: 1 / 3; display: flex; flex-direction: column; gap: 6px; }
        .col-center { grid-column: 2; grid-row: 1; display: flex; flex-direction: column; gap: 6px; }
        .col-right { grid-column: 3; grid-row: 1; display: flex; flex-direction: column; gap: 6px; }
        .row-ibov { grid-column: 2 / 4; grid-row: 2; }
        .flex-1 { flex: 1; }
        .min-h-0 { min-height: 0; }

        .ibov-container::-webkit-scrollbar { height: 3px; }
        .ibov-container::-webkit-scrollbar-track { background: #1A2538; }
        .ibov-container::-webkit-scrollbar-thumb { background: #5E7390; border-radius: 3px; }

        @media (max-width: 1024px) {
            .main-grid { grid-template-columns: 1fr; gap: 6px; }
            .col-left, .col-center, .col-right, .row-ibov { grid-column: 1; grid-row: auto; }
            .duo-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
            .topbar { flex-direction: column; align-items: stretch; text-align: center; }
            .topbar-left { justify-content: center; }
            .topbar-right { justify-content: center; flex-wrap: wrap; }
            .pv-grid { grid-template-columns: 1fr; }
            .duo-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="container">
    <!-- TOP BAR -->
    <div class="topbar">
        <div class="topbar-left">
            <span class="live-dot"></span>
            <span class="topbar-title">SMART TRADE <span>— Mini Índice</span></span>
        </div>
        <div class="topbar-right">
            <span class="topbar-status" id="statusBadge">● Online</span>
            <span class="topbar-time" id="clock">--:--:-- · Ao vivo</span>
        </div>
    </div>

    <!-- CONTEÚDO -->
    <div id="content">
        <!-- O conteúdo será injetado pelo JavaScript com os dados do servidor -->
    </div>
</div>

<script>
// ============================================
// DADOS RECEBIDOS DO SERVIDOR
// ============================================
const DADOS_SERVIDOR = {DADOS_JSON};

// ============================================
// FUNÇÕES DE FORMATAÇÃO
// ============================================
function fmtNum(valor) {
    if (typeof valor === 'number') {
        return valor > 0 ? '+' + valor.toFixed(0).replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.') : valor.toFixed(0).replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.');
    }
    return valor;
}

function fmtPct(valor) {
    if (typeof valor === 'number') {
        return (valor > 0 ? '+' : '') + valor.toFixed(2) + '%';
    }
    return valor;
}

function clsValor(valor) {
    if (typeof valor === 'number') {
        return valor > 0 ? 'pos' : valor < 0 ? 'neg' : 'gray';
    }
    return 'gray';
}

function clsValorBar(valor) {
    if (typeof valor === 'number') {
        return valor >= 0 ? 'green' : 'red';
    }
    return 'gray';
}

// ============================================
// RENDERIZAÇÃO
// ============================================
function renderizarCard(titulo, itens, classe = '') {
    if (!itens || Object.keys(itens).length === 0) return '';
    let html = `<div class="card"><div class="card-title ${classe}">${titulo}</div>`;
    for (const [label, valor] of Object.entries(itens)) {
        const classeValor = clsValor(valor);
        const texto = typeof valor === 'number' ? fmtPct(valor) : valor;
        html += `<div class="row-item"><span class="row-label">${label}</span><span class="row-value ${classeValor}">${texto}</span></div>`;
    }
    html += '</div>';
    return html;
}

function renderizarBarras(titulo, itens) {
    if (!itens || Object.keys(itens).length === 0) return '';
    let html = `<div class="card"><div class="card-title">${titulo}</div>`;
    for (const [label, valor] of Object.entries(itens)) {
        const classe = clsValorBar(valor);
        const pct = Math.min(Math.abs(valor) / 20000 * 100, 90);
        const lado = valor >= 0 ? 'left:50%;' : 'right:50%;';
        const clsText = valor >= 0 ? 'pos' : 'neg';
        html += `
            <div class="bar-wrap">
                <div class="bar-label"><span>${label}</span><span class="val ${clsText}">${fmtNum(valor)}</span></div>
                <div class="bar-track"><div class="bar-fill ${classe}" style="width:${pct}%;${lado}"></div></div>
            </div>
        `;
    }
    html += '</div>';
    return html;
}

function renderizarTabela(titulo, dados, classe) {
    if (!dados || dados.length === 0) return '';
    let html = `<div class="card"><div class="card-title ${classe}">${titulo}</div><table class="table-mini"><thead><tr><th>Corretora</th><th>Qtd</th></tr></thead><tbody>`;
    for (const item of dados) {
        const cls = item.qtd >= 0 ? 'pos' : 'neg';
        html += `<tr><td>${item.corretora}</td><td class="${cls}">${fmtNum(item.qtd)}</td></tr>`;
    }
    html += '</tbody></table></div>';
    return html;
}

function renderizarProgresso(titulo, dados) {
    if (!dados || dados.length === 0) return '';
    let html = `<div class="card" style="flex:1;min-height:0;"><div class="card-title">${titulo}</div>`;
    const maxAbs = Math.max(...dados.map(d => Math.abs(d.variacao)), 0.01);
    for (const item of dados) {
        const cls = item.variacao >= 0 ? 'green' : 'red';
        const pct = Math.abs(item.variacao) / maxAbs * 100;
        const pctCls = item.variacao >= 0 ? 'pos' : 'neg';
        html += `
            <div class="progress-item">
                <span class="progress-label">${item.ticker}</span>
                <div class="progress-track"><div class="progress-fill ${cls}" style="width:${Math.max(pct, 2)}%;"></div></div>
                <span class="progress-pct ${pctCls}">${fmtPct(item.variacao)}</span>
            </div>
        `;
    }
    html += '</div>';
    return html;
}

function renderizarPetrVale(dados) {
    if (!dados || Object.keys(dados).length === 0) return '';
    let html = `<div class="card"><div class="card-title">Petr &amp; Vale</div><div class="pv-grid">`;
    for (const [ticker, valor] of Object.entries(dados)) {
        const cls = valor >= 0 ? 'pos' : 'neg';
        html += `<div class="pv-item"><div class="ticker">${ticker}</div><div class="change ${cls}">${fmtPct(valor)}</div></div>`;
    }
    html += '</div></div>';
    return html;
}

function renderizarIbov(acoes) {
    if (!acoes || acoes.length === 0) return '';
    const maxHeight = 50;
    const valores = acoes.map(() => (Math.random() - 0.48) * 5);
    const maxAbs = Math.max(...valores.map(v => Math.abs(v)), 0.01);
    
    let html = `<div class="card"><div class="card-title">Ações IBOV</div><div class="ibov-container"><div class="ibov-wrap">`;
    for (let i = 0; i < acoes.length; i++) {
        const v = valores[i];
        const isPositive = v >= 0;
        const color = isPositive ? '#1DB954' : '#E63946';
        const height = Math.max(Math.min(Math.abs(v) / maxAbs * maxHeight, maxHeight), 1);
        html += `
            <div class="ibov-col" title="${acoes[i]}: ${v > 0 ? '+' : ''}${v.toFixed(2)}%">
                <div style="height:${maxHeight}px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <div style="height:${isPositive ? (maxHeight/2 - height/2) : (maxHeight/2)}px;"></div>
                    <div class="ibov-bar" style="height:${height}px;background:${color};"></div>
                    <div style="height:${isPositive ? (maxHeight/2) : (maxHeight/2 - height/2)}px;"></div>
                </div>
                <div class="ibov-label">${acoes[i]}</div>
            </div>
        `;
    }
    html += '</div></div></div>';
    return html;
}

// ============================================
// DASHBOARD
// ============================================
function renderizarDashboard(dados) {
    const container = document.getElementById('content');
    
    const html = `
        <div class="main-grid">
            <div class="col-left">
                <div class="card" style="display:flex;align-items:center;justify-content:center;padding:12px;min-height:60px;">
                    <div style="text-align:center;">
                        <div style="font-size:14px;font-weight:800;color:#E8EDF5;letter-spacing:0.08em;">SMART TRADE</div>
                        <div style="font-size:8px;color:#5E7390;">Decisões mais precisas</div>
                    </div>
                </div>
                ${renderizarCard('Cotações Atuais', dados.cotacoes)}
                ${renderizarCard('Informações Índice', dados.informacoes_indice)}
                ${renderizarCard('Movimento do Mercado', dados.movimento_mercado)}
                ${renderizarBarras('Saldo Dólar — Diário', dados.saldo_dolar)}
                <div class="card" style="flex:1;min-height:0;">
                    <div class="card-title">Termômetro da Força</div>
                    <div class="thermo-wrap">
                        <canvas id="gauge" width="130" height="72"></canvas>
                    </div>
                </div>
            </div>

            <div class="col-center">
                ${renderizarBarras('Saldo Diário — Mini Índice', dados.saldo_diario)}
                <div class="duo-grid">
                    ${renderizarTabela('▼ Top Vendidos', dados.top_vendidos, 'red')}
                    ${renderizarTabela('▲ Top Comprados', dados.top_comprados, 'green')}
                </div>
                ${renderizarBarras('Saldo 5 Min — Mini Índice', dados.saldo_5min)}
                <div class="duo-grid" style="flex:1;min-height:0;">
                    <div class="card"><div class="card-title red">▼ Vendidos 5 Min</div><div style="color:#5E7390;font-size:9px;text-align:center;padding:8px 0;">Sem dados</div></div>
                    <div class="card"><div class="card-title green">▲ Comprados 5 Min</div><div style="color:#5E7390;font-size:9px;text-align:center;padding:8px 0;">Sem dados</div></div>
                </div>
            </div>

            <div class="col-right">
                ${renderizarPetrVale(dados.petr_vale)}
                ${renderizarProgresso('Top 10 Ações', dados.top_10_acoes)}
                ${renderizarProgresso('Setor Financeiro', dados.setor_financeiro)}
            </div>

            <div class="row-ibov">
                ${renderizarIbov(dados.acoes_ibov)}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    setTimeout(drawGauge, 100);
}

// ============================================
// GAUGE
// ============================================
function drawGauge() {
    const canvas = document.getElementById('gauge');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cx = 65, cy = 65, r = 52;

    ctx.clearRect(0, 0, 130, 72);

    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, 2 * Math.PI);
    ctx.lineWidth = 11;
    ctx.strokeStyle = '#1A2538';
    ctx.stroke();

    const segments = [
        { color: '#E63946', start: Math.PI, end: Math.PI * 1.4 },
        { color: '#F4A020', start: Math.PI * 1.4, end: Math.PI * 1.6 },
        { color: '#1DB954', start: Math.PI * 1.6, end: Math.PI * 2 }
    ];

    segments.forEach(seg => {
        ctx.beginPath();
        ctx.arc(cx, cy, r, seg.start, seg.end);
        ctx.lineWidth = 11;
        ctx.strokeStyle = seg.color;
        ctx.stroke();
    });

    const angle = Math.PI + 0.3 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * 38, cy + Math.sin(angle) * 38);
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#E8EDF5';
    ctx.lineCap = 'round';
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
    ctx.fillStyle = '#E8EDF5';
    ctx.fill();
}

// ============================================
// RELÓGIO
// ============================================
function updateClock() {
    const now = new Date();
    const time = now.toLocaleTimeString('pt-BR', { hour12: false });
    document.getElementById('clock').textContent = time + ' · Ao vivo';
}
updateClock();
setInterval(updateClock, 1000);

// ============================================
// CARREGAR DADOS ATUALIZADOS DA API
// ============================================
async function atualizarDados() {
    const statusBadge = document.getElementById('statusBadge');
    
    try {
        const response = await fetch('/api/dados');
        if (response.ok) {
            const data = await response.json();
            if (data.dados && Object.keys(data.dados).length > 0) {
                // Mescla os dados novos com os existentes
                for (const [chave, valor] of Object.entries(data.dados)) {
                    if (chave in DADOS_SERVIDOR && typeof DADOS_SERVIDOR[chave] === 'object' && typeof valor === 'object') {
                        Object.assign(DADOS_SERVIDOR[chave], valor);
                    } else {
                        DADOS_SERVIDOR[chave] = valor;
                    }
                }
                renderizarDashboard(DADOS_SERVIDOR);
                statusBadge.textContent = '● Online';
                statusBadge.style.color = '#1DB954';
                return;
            }
        }
        statusBadge.textContent = '● Offline';
        statusBadge.style.color = '#E63946';
    } catch (e) {
        statusBadge.textContent = '● Offline';
        statusBadge.style.color = '#E63946';
    }
}

// ============================================
// INICIALIZAÇÃO
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Renderiza com os dados do servidor
    renderizarDashboard(DADOS_SERVIDOR);
    
    // Tenta atualizar da API em segundo plano
    setTimeout(atualizarDados, 2000);
    setInterval(atualizarDados, 30000);
});
</script>

</body>
</html>
"""

@app.get("/")
async def index():
    """Página principal com dados embutidos"""
    # Converte os dados para JSON para injetar no HTML
    dados_json = json.dumps(latest_data, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("{DADOS_JSON}", dados_json)
    return HTMLResponse(html)

@app.get("/index.html")
async def index_html():
    """Redireciona /index.html para /"""
    return await index()

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
