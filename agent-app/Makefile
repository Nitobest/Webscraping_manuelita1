.PHONY: help setup install run dev test clean lint format docs

# Variables
PYTHON := python3
PIP := pip
UV := uv

help:
	@echo "=================================="
	@echo "Agent-App Makefile Commands"
	@echo "=================================="
	@echo "setup           - Instalar dependencias con UV"
	@echo "install         - Instalar con pip"
	@echo "run             - Ejecutar aplicación Streamlit"
	@echo "dev             - Ejecutar en modo desarrollo"
	@echo "test            - Ejecutar tests"
	@echo "lint            - Ejecutar linter"
	@echo "format          - Formatear código"
	@echo "clean           - Limpiar archivos temporales"
	@echo "generate-faq    - Generar FAQ JSON desde markdown"
	@echo "help            - Mostrar esta ayuda"

setup:
	@echo "Instalando dependencias con UV..."
	$(UV) sync
	@echo "✅ Setup completado"

install:
	@echo "Instalando dependencias con pip..."
	$(PIP) install -e ".[dev]"
	@echo "✅ Instalación completada"

run:
	@echo "🚀 Iniciando aplicación Streamlit..."
	streamlit run app.py

dev:
	@echo "🔧 Modo desarrollo - Hot reload activo..."
	streamlit run app.py --logger.level=debug

test:
	@echo "🧪 Ejecutando tests..."
	$(PYTHON) -m pytest tests/ -v --cov=. --cov-report=html
	@echo "✅ Tests completados. Reporte HTML en htmlcov/"

lint:
	@echo "🔍 Ejecutando linter..."
	flake8 . --exclude=venv,.venv
	@echo "✅ Lint completado"

format:
	@echo "🎨 Formateando código..."
	black . --exclude=venv,.venv
	@echo "✅ Formato completado"

clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✅ Limpieza completada"

generate-faq:
	@echo "🔄 Generando FAQ JSON desde markdown..."
	$(PYTHON) parser.py
	@echo "✅ FAQ JSON generado en tools/data/faq_structured.json"

# Alias útiles
.PHONY: test-quick
test-quick:
	$(PYTHON) -m pytest tests/ -v --tb=short

.PHONY: docker-build
docker-build:
	@echo "🐳 Construyendo imagen Docker..."
	docker build -t agent-app:latest .

.PHONY: docker-run
docker-run:
	@echo "🐳 Ejecutando en Docker..."
	docker run -p 8501:8501 agent-app:latest

.DEFAULT_GOAL := help
