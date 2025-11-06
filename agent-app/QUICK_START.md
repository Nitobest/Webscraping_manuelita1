# 🚀 QUICK START - Agent-App

## ⚡ 5 Pasos para Ejecutar

### 1️⃣ Instalar Dependencias

**Opción A: Windows PowerShell (Recomendado)**
```powershell
.\setup.ps1
```

**Opción B: Manual con pip**
```bash
pip install python-dotenv streamlit langchain langchain-community pydantic
pip install chromadb sentence-transformers rank-bm25 langchain-huggingface
pip install beautifulsoup4 html2text requests lxml
```

### 2️⃣ Configurar Credenciales

```bash
# Copiar template
copy .env.example .env

# Editar .env y añadir tu API key
# OPENAI_API_KEY=sk-proj-tu-clave-aqui
```

### 3️⃣ Generar FAQ JSON (Opcional)

```bash
python parser.py
```

Esto extrae automáticamente datos de `../data/raw/processed/` y crea:
- `tools/data/faq_structured.json`

### 4️⃣ Ejecutar la Aplicación

```bash
streamlit run app.py
```

Se abrirá en `http://localhost:8501`

### 5️⃣ ¡Listo!

Navega por las 3 ventanas:
- **❓ FAQs**: Ejemplos de preguntas
- **⚙️ Admin**: Configurar parámetros
- **💬 Chat**: Conversación interactiva

---

## 📋 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'streamlit'` | `pip install streamlit` |
| `ModuleNotFoundError: No module named 'dotenv'` | `pip install python-dotenv` |
| `Error: 'OPENAI_API_KEY' not found` | Edita `.env` y añade tu API key |
| `Vectorstore not available` | Corre `python parser.py` primero |
| Puerto 8501 ya en uso | `streamlit run app.py --server.port 8502` |

---

## 🧪 Tests Rápidos

```bash
# Todos los tests
pytest tests/ -v

# Solo tests de memoria
pytest tests/test_agent.py::TestMemory -v

# Solo tests de enrutamiento
pytest tests/test_agent.py::TestRouting -v
```

---

## 🎛️ Parámetros Configurables

En **Admin Panel → Configuración**:

| Parámetro | Rango | Default |
|-----------|-------|---------|
| Temperatura | 0.0-1.0 | 0.05 |
| Top K | 1-10 | 4 |
| Max Tokens | 100-2000 | 500 |
| Streaming Speed | 10-200ms | 50 |
| Memory Tokens | 5K-50K | 20K |
| Icono Streaming | 11 opciones | 🐢 |

---

## 💡 Ejemplos de Uso

### Pregunta RAG
```
"¿Cuál es la historia de Manuelita?"
↓
Sistema RAG busca en documentos
↓
Respuesta: "Manuelita fue fundada en 1864..."
```

### Pregunta Structured
```
"¿Cuál es el teléfono?"
↓
Busca en JSON estructurado
↓
Respuesta: "(602) 889-1444"
```

### Pregunta con Memoria
```
Q1: "¿Quién es Manuelita?"
Q2: "¿Cuántas sedes tienen?" ← Usa contexto de Q1
```

---

## 📊 Comandos Útiles

```bash
# Ver configuración
python config.py

# Generar FAQ
python parser.py

# Tests
pytest tests/ -v

# Limpiar
make clean

# Formato código
black .

# Linter
flake8 .
```

---

## 🆘 Soporte Rápido

**Dependencias faltando:**
```bash
pip install -e ".[dev]"
```

**Versión de Python:**
```bash
python --version  # Debe ser 3.9+
```

**Tests rápidos:**
```bash
pytest tests/test_agent.py::TestMemory::test_memory_creation -v
```

---

**¡Listo para usar! 🎉**
