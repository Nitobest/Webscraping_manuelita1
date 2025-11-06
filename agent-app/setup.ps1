# =============================================================================
# Setup Script para Agent-App (PowerShell)
# =============================================================================

Write-Host "🚀 Iniciando setup de Agent-App..." -ForegroundColor Cyan

# 1. Instalar dependencias principales
Write-Host "`n📦 Instalando dependencias principales..." -ForegroundColor Yellow
pip install python-dotenv streamlit langchain langchain-community pydantic

# 2. Instalar dependencias de RAG
Write-Host "`n🔍 Instalando dependencias de RAG..." -ForegroundColor Yellow
pip install chromadb sentence-transformers rank-bm25 langchain-huggingface

# 3. Instalar dependencias de web scraping
Write-Host "`n🌐 Instalando dependencias de web scraping..." -ForegroundColor Yellow
pip install beautifulsoup4 html2text requests lxml

# 4. Crear .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "`n📝 Creando archivo .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Archivo .env creado. Por favor, edítalo y añade tu OPENAI_API_KEY"
} else {
    Write-Host "`n✅ Archivo .env ya existe" -ForegroundColor Green
}

# 5. Crear directorios necesarios
Write-Host "`n📁 Creando directorios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "vectordb" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "tools/data" | Out-Null

# 6. Resumen
Write-Host "`n✅ Setup completado!" -ForegroundColor Green
Write-Host "`n📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Editar .env: nano .env (o tu editor favorito)" 
Write-Host "2. Añadir OPENAI_API_KEY o GOOGLE_API_KEY"
Write-Host "3. Generar FAQ JSON: python parser.py"
Write-Host "4. Ejecutar app: streamlit run app.py"
Write-Host ""
