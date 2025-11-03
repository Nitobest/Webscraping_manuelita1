# 🚨 Solución de Problemas - Chat No Responde

## Problema Identificado

El chat no responde porque **`OPENAI_API_KEY` no está configurada**.

### Debug Output
```
OpenAI API Key configurada: False
Google API Key configurada: False
LLM Available: False
```

---

## ✅ Solución

### Opción 1: Crear archivo `.env` (Recomendado)

1. **En el directorio `agent-app/`, crea un archivo llamado `.env`**

2. **Agrega tu API key de OpenAI:**
```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
```

3. **Obtén tu API key en:** https://platform.openai.com/api-keys

4. **Reinicia Streamlit:**
```bash
streamlit run app.py
```

---

### Opción 2: Variable de Entorno Global (PowerShell)

Si prefieres configurar globalmente sin crear `.env`:

```powershell
$env:OPENAI_API_KEY = "sk-tu-api-key-aqui"
streamlit run app.py
```

---

### Opción 3: Usar Google Gemini en lugar de OpenAI

Si no tienes API key de OpenAI, puedes usar Google Gemini:

1. **Obtén API key en:** https://ai.google.dev/

2. **En `.env`, agrega:**
```bash
GOOGLE_API_KEY=tu-google-api-key-aqui
```

3. **En Admin Panel → Configuración, selecciona:**
   - Proveedor: `Google Gemini`
   - Modelo: `gemini-2.5-pro` (o tu modelo preferido)

---

## 📋 Requisitos de Dependencias

**Para OpenAI:**
```bash
pip install langchain-openai
```

**Para Google Gemini:**
```bash
pip install langchain-google-genai
```

**Ambos están en `requirements.txt`, instálalos con:**
```bash
pip install -r requirements.txt
```

---

## 🔍 Verificar Configuración

Ejecuta el script de debug:

```bash
python debug_chat.py
```

Deberías ver:
```
OpenAI API Key configurada: True  ✅
LLM Available: True  ✅
```

---

## 📝 Nota Importante

**No commits `.env` con API keys reales.** El archivo `.env` está en `.gitignore` para seguridad.

---

## ⚡ Quick Fix Summary

1. Copia `.env.example` → `.env`
2. Reemplaza `OPENAI_API_KEY` con tu clave real
3. Reinicia Streamlit
4. El chat debería responder ahora 🚀
