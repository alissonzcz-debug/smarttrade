# ============================================
# SERVE ARQUIVOS ESTÁTICOS (Frontend)
# ============================================

# Verifica se existe a pasta 'client'
if os.path.exists("client") and os.path.exists("client/index.html"):
    logger.info("📁 Servindo frontend da pasta 'client'")
    app.mount("/", StaticFiles(directory="client", html=True), name="static")
else:
    logger.warning("⚠️ Frontend não encontrado")
    
    @app.get("/")
    async def root_fallback():
        return HTMLResponse("""
            <html>
                <head><title>Smart Trade</title></head>
                <body style="background:#0A0E17;color:#E8EDF5;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
                    <div style="text-align:center;">
                        <h1>📊 Smart Trade</h1>
                        <p style="color:#1DB954;">✅ API online!</p>
                        <p style="color:#5E7390;">Frontend não encontrado. Crie a pasta <code>client/</code> com <code>index.html</code></p>
                        <br>
                        <a href="/api/status" style="color:#1DB954;">▶ Status da API</a>
                    </div>
                </body>
            </html>
        """)
