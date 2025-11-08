# 🔍 Guía de Integración LangSmith - Fase 1

## ¿Qué es LangSmith?

LangSmith es la plataforma de observabilidad de LangChain que te permite:

- 📊 **Trazar** todas las interacciones del agente en tiempo real
- 🐛 **Debuggear** problemas de prompts, llamadas a LLM y RAG
- 📈 **Medir** latencia, tokens consumidos, costos y tasas de éxito
- 🔬 **Evaluar** respuestas del agente con datasets de prueba
- 🚀 **Optimizar** prompts basándote en datos reales

---

## ✅ Fase 1: Setup Básico (ACTUAL)

### Estado Actual
- ✅ Dependencia `langsmith>=0.1.0` agregada a `pyproject.toml`
- ✅ Variables de entorno configuradas en `.env.example`
- ✅ Módulo `langsmith_config.py` creado
- ⏸️ **LangSmith está DESHABILITADO por defecto** (no afecta funcionamiento actual)

---

## 🚀 Cómo Habilitar LangSmith

### Paso 1: Obtener API Key

1. Ve a [smith.langchain.com](https://smith.langchain.com)
2. Crea una cuenta (gratis)
3. Ve a **Settings** → **API Keys**
4. Crea una nueva API key
5. Cópiala (formato: `lsv2_pt_...`)

### Paso 2: Configurar Variables de Entorno

Edita tu archivo `.env` y agrega:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_tu-api-key-aqui
LANGCHAIN_PROJECT=manuelita-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### Paso 3: Instalar Dependencia

```powershell
# Con UV (recomendado)
uv pip install langsmith

# O con pip
pip install langsmith
```

### Paso 4: Verificar Configuración

```powershell
python langsmith_config.py
```

Deberías ver:

```
============================================================
🔍 LANGSMITH OBSERVABILITY HABILITADA
============================================================
📊 Proyecto: manuelita-agent
🔑 API Key: ✅ Configurada
🌐 Endpoint: https://api.smith.langchain.com
📍 Ver trazas en: https://smith.langchain.com
============================================================
```

### Paso 5: Reiniciar la Aplicación

```powershell
streamlit run app.py
```

---

## 📊 ¿Qué Verás en LangSmith?

Una vez habilitado, cada interacción del usuario se trazará automáticamente:

### 1. **Trazas de Conversaciones**
- Pregunta del usuario
- Contexto RAG recuperado
- Prompt completo enviado al LLM
- Respuesta generada
- Tiempo de ejecución
- Tokens consumidos

### 2. **Métricas Automáticas**
- Latencia por componente (RAG, LLM, Memoria)
- Costo por query (tokens * precio)
- Tasa de éxito/fallo
- Uso de herramientas (RAG vs Structured)

### 3. **Debugging Visual**
- Ver exactamente qué documentos recuperó RAG
- Ver el prompt final enviado al LLM
- Ver la cadena completa de razonamiento

---

## 🎯 Casos de Uso Inmediatos

### 1. Debuggear Respuestas Incorrectas

**Antes (sin LangSmith):**
```
Usuario: "¿Cuánto cuesta el azúcar?"
Agente: "No tengo esa información"
❌ No sabes POR QUÉ falló
```

**Con LangSmith:**
```
📊 Traza muestra:
  - RAG recuperó documentos irrelevantes (mal embedding)
  - Prompt no incluyó suficiente contexto
  - LLM recibió información incompleta
✅ Ahora sabes EXACTAMENTE dónde está el problema
```

### 2. Optimizar Rendimiento

```
📈 Dashboard LangSmith muestra:
  - RAG toma 1.2s (muy lento)
  - LLM toma 0.3s (ok)
  - Total: 1.5s por query
  
🎯 Acción: Reducir Top K de 4 a 2
✅ Resultado: 1.5s → 0.8s (47% más rápido)
```

### 3. Medir Costos Reales

```
📊 LangSmith muestra:
  - 1,234 queries en última semana
  - 450K tokens totales
  - Costo estimado: $2.25 USD
  
💡 Insight: Puedes proyectar costos mensuales reales
```

---

## 🔒 Seguridad y Privacidad

### ¿Qué se envía a LangSmith?

- ✅ Estructura de las llamadas (trazas)
- ✅ Inputs/outputs del agente
- ✅ Métricas de rendimiento
- ❌ **NO se envían API keys de OpenAI/Google**
- ❌ **NO se comparten datos fuera de tu cuenta**

### Deshabilitar Temporalmente

```python
# En código
from langsmith_config import langsmith_config
langsmith_config.disable()

# O en .env
LANGCHAIN_TRACING_V2=false
```

---

## 📋 Checklist de Fase 1

- [ ] Crear cuenta en smith.langchain.com
- [ ] Obtener API key
- [ ] Configurar `.env` con `LANGCHAIN_TRACING_V2=true`
- [ ] Instalar `langsmith` con `uv pip install langsmith`
- [ ] Ejecutar `python langsmith_config.py` para verificar
- [ ] Reiniciar Streamlit
- [ ] Hacer 3-5 preguntas en el chat
- [ ] Ir a smith.langchain.com y ver trazas

---

## 🎓 Recursos

- **Documentación oficial:** [docs.smith.langchain.com](https://docs.smith.langchain.com)
- **Video tutorial:** [youtube.com/watch?v=LangSmith](https://www.youtube.com/results?search_query=langsmith+tutorial)
- **Pricing:** Plan gratuito incluye 5,000 trazas/mes

---

## ⏭️ Próximos Pasos (Fase 2)

Una vez que estés cómodo con Fase 1, podemos avanzar a:

### Fase 2: Instrumentación Core
- Agregar trazas manuales en `agent.py`
- Trackear métricas personalizadas (tool usage, memory hits)
- Crear dashboards específicos para Manuelita

### Fase 3: Optimización Avanzada
- Evaluación automática con datasets
- A/B testing de prompts
- Alertas automáticas ante degradación

---

## ❓ Troubleshooting

### Error: "API key inválida"
```powershell
# Verificar que copiaste la key completa
echo $env:LANGCHAIN_API_KEY

# Debe empezar con: lsv2_pt_
```

### No aparecen trazas en LangSmith
```powershell
# 1. Verificar que LANGCHAIN_TRACING_V2=true
python langsmith_config.py

# 2. Verificar que app.py cargó las variables
# Agrega al inicio de app.py:
from langsmith_config import log_langsmith_info
log_langsmith_info()
```

### Ralentiza la aplicación
```bash
# LangSmith agrega ~50-100ms por traza
# Si es crítico, deshabilita en producción:
LANGCHAIN_TRACING_V2=false
```

---

## 📞 Contacto

Si tienes dudas sobre la integración:
1. Revisa logs en consola
2. Ejecuta `python langsmith_config.py`
3. Consulta [docs.smith.langchain.com](https://docs.smith.langchain.com)

---

**Fase 1 completada.** LangSmith está listo para usar cuando decidas habilitarlo. 🎉
