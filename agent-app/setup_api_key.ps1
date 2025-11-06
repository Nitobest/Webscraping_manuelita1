# ============================================================================
# Script para Configurar API Key de OpenAI
# ============================================================================

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Configurador de API Key" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$env_file = ".env"

# Verificar si .env ya existe
if (Test-Path $env_file) {
    Write-Host "✅ Archivo .env ya existe" -ForegroundColor Green
    $overwrite = Read-Host "¿Deseas reemplazarlo? (s/n)"
    if ($overwrite -ne "s") {
        Write-Host "Cancelado." -ForegroundColor Yellow
        exit
    }
}

# Pedir API Key
Write-Host ""
Write-Host "🔑 Ingresa tu API Key de OpenAI" -ForegroundColor Cyan
Write-Host "   Obtén una en: https://platform.openai.com/api-keys" -ForegroundColor Gray
$api_key = Read-Host "   API Key"

if ($api_key -eq "") {
    Write-Host "❌ No ingresaste una API Key" -ForegroundColor Red
    exit
}

# Copiar .env.example si existe
if (Test-Path ".env.example") {
    Copy-Item ".env.example" $env_file
    Write-Host "✅ Copiado .env.example → .env" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env.example no encontrado, creando .env nuevo" -ForegroundColor Yellow
}

# Reemplazar API Key en .env
if (Test-Path $env_file) {
    $content = Get-Content $env_file
    # Reemplazar la línea de OPENAI_API_KEY
    $content = $content -replace "OPENAI_API_KEY=.*", "OPENAI_API_KEY=$api_key"
    Set-Content $env_file $content
    Write-Host "✅ API Key configurada en .env" -ForegroundColor Green
} else {
    @"
# OpenAI API Key
OPENAI_API_KEY=$api_key

# Google Gemini (opcional)
GOOGLE_API_KEY=

# Data Configuration
DATA_DIR=../data/raw/processed
VECTORDB_DIR=./vectordb
STRUCTURED_DATA_FILE=tools/data/faq_structured.json
"@ | Set-Content $env_file
    Write-Host "✅ Archivo .env creado" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "  ✅ Configuración Completada" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Inicia Streamlit: streamlit run app.py"
Write-Host "2. Ve a la ventana 💬 Chat"
Write-Host "3. El chat debería responder ahora"
Write-Host ""
