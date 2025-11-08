"""
Aplicación Streamlit - Asistente Inteligente Manuelita

3 Ventanas: FAQs, Admin, Chat Interactivo
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from agent import ManuelitaAgent
from config import config, SAMPLE_FAQS
from memory import SessionManager
from parser import create_faq_json

# ============================================================================
# CONFIGURACIÓN STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Manuelita Insight | Asistente Inteligente",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar CSS personalizado con colores corporativos
def load_custom_css():
    """Carga CSS personalizado con tema Manuelita."""
    css_file = Path(".streamlit/custom.css")
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_custom_css()

# ============================================================================
# INICIALIZACIÓN DE ESTADO
# ============================================================================

if 'current_provider' not in st.session_state:
    st.session_state.current_provider = config.llm.provider

if 'agent' not in st.session_state:
    st.session_state.agent = ManuelitaAgent(provider=st.session_state.current_provider)
else:
    # Si el proveedor cambió en config, reinicializa el agente
    if config.llm.provider != st.session_state.current_provider:
        st.session_state.current_provider = config.llm.provider
        st.session_state.agent = ManuelitaAgent(provider=config.llm.provider)

if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()
    st.session_state.session_manager.create_conversation("Conversación 1")

if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = "Conversación 1"

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'json_generated' not in st.session_state:
    st.session_state.json_generated = False

if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None

if 'switch_to_chat' not in st.session_state:
    st.session_state.switch_to_chat = False

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def stream_response(text: str, speed_ms: int = 50) -> None:
    """Simula streaming de respuesta carácter por carácter con icono generador.
    
    Args:
        text: Texto a mostrar
        speed_ms: Velocidad en ms por carácter (10=rápido, 200=lento)
    """
    delay_sec = speed_ms / 1000.0
    placeholder = st.empty()
    streamed_text = ""
    
    # Streaming con icono como "cursor" generador
    for char in text:
        streamed_text += char
        # Mostrar texto + icono al final (como cursor)
        placeholder.markdown(f"{streamed_text} {config.streaming.icon}")
        time.sleep(delay_sec)
    
    # Resultado final: solo el texto, sin icono
    placeholder.markdown(streamed_text)

def process_user_input(question: str, memory_context: str = "") -> Dict[str, Any]:
    """Procesa entrada del usuario.
    
    Args:
        question: Pregunta del usuario
        memory_context: Contexto de memoria de la conversación actual
    """
    try:
        # Inyectar memoria de conversación en el agente temporalmente
        original_memory_context = st.session_state.agent.get_memory_context()
        
        # Si hay contexto de conversación, usarlo para generar respuesta
        if memory_context:
            # Modificar temporalmente get_memory_context para devolver el contexto actual
            st.session_state.agent.get_memory_context = lambda: memory_context
        
        result = st.session_state.agent.process(
            question=question,
            use_memory=False,  # No usar memoria del agente, pasamos contexto manualmente
            temperature=config.llm.temperature,
            top_k=config.llm.top_k,
            max_tokens=config.llm.max_tokens
        )
        
        # Restaurar método original
        if memory_context:
            st.session_state.agent.get_memory_context = lambda: original_memory_context
        
        return result
    except Exception as e:
        logger.error(f"Error procesando input: {e}")
        return {
            'question': question,
            'answer': f"Error: {str(e)}",
            'tool_used': 'error',
            'success': False
        }

def generate_faq_json() -> bool:
    """Genera JSON de FAQ desde markdown."""
    try:
        success = create_faq_json(
            markdown_dir=config.data_dir,
            output_path=config.structured_data_file
        )
        return success
    except Exception as e:
        logger.error(f"Error generando FAQ JSON: {e}")
        return False

# ============================================================================
# VENTANA 1: FAQs
# ============================================================================

def page_faqs():
    """Página de FAQs para probar el sistema."""
    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg, #00A651 0%, #008C45 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
        ">
            <h1 style="margin: 0; color: white; font-size: 2rem;">
                🧪 Pruebas del Sistema
            </h1>
            <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">
                Valida cada componente del asistente inteligente
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.info(
        "🎯 **Objetivo:** Estas preguntas están diseñadas para probar diferentes aspectos del agente.\n\n"
        "Haz clic en 'Probar' para ir al Chat y hacer la pregunta automáticamente."
    )
    
    st.divider()
    
    # Agrupar por tipo de prueba
    test_types = {
        "rag": [],
        "structured": [],
        "memory": [],
        "routing": []
    }
    
    for faq in SAMPLE_FAQS:
        test_types[faq['type']].append(faq)
    
    # SECCIÓN 1: PRUEBA RAG
    if test_types['rag']:
        st.markdown("### 📚 Prueba de RAG (Retrieval-Augmented Generation)")
        st.caption("Verifica que el sistema recupere información desde la base vectorial")
        
        for i, faq in enumerate(test_types['rag']):
            with st.container():
                col1, col2, col3 = st.columns([0.3, 3, 1])
                with col1:
                    st.markdown(f"### {faq['icon']}")
                with col2:
                    st.markdown(f"**{faq['question']}**")
                    st.caption(faq['test_purpose'])
                with col3:
                    if st.button("🚀 Probar", key=f"faq_rag_{i}"):
                        st.session_state.pending_question = faq['question']
                        st.session_state.switch_to_chat = True
                        st.rerun()
        st.divider()
    
    # SECCIÓN 2: PRUEBA STRUCTURED
    if test_types['structured']:
        st.markdown("### 📊 Prueba de Herramienta Estructurada")
        st.caption("Verifica que el router seleccione datos estructurados para preguntas directas")
        
        for i, faq in enumerate(test_types['structured']):
            with st.container():
                col1, col2, col3 = st.columns([0.3, 3, 1])
                with col1:
                    st.markdown(f"### {faq['icon']}")
                with col2:
                    st.markdown(f"**{faq['question']}**")
                    st.caption(faq['test_purpose'])
                with col3:
                    if st.button("🚀 Probar", key=f"faq_structured_{i}"):
                        st.session_state.pending_question = faq['question']
                        st.session_state.switch_to_chat = True
                        st.rerun()
        st.divider()
    
    # SECCIÓN 3: PRUEBA MEMORIA
    if test_types['memory']:
        st.markdown("### 🧠 Prueba de Memoria Conversacional")
        st.caption("Verifica que el sistema recuerde información de turnos anteriores")
        
        st.warning(
            "⚠️ **Importante:** Estas preguntas deben hacerse en secuencia para probar la memoria correctamente.\n"
            "Haz la primera, espera la respuesta, luego haz la segunda."
        )
        
        for i, faq in enumerate(test_types['memory']):
            with st.container():
                col1, col2, col3 = st.columns([0.3, 3, 1])
                with col1:
                    st.markdown(f"### {faq['icon']}")
                with col2:
                    st.markdown(f"**{i+1}. {faq['question']}**")
                    st.caption(faq['test_purpose'])
                with col3:
                    if st.button("🚀 Probar", key=f"faq_memory_{i}"):
                        st.session_state.pending_question = faq['question']
                        st.session_state.switch_to_chat = True
                        st.rerun()
        st.divider()
    
    # SECCIÓN 4: PRUEBA ROUTING
    if test_types['routing']:
        st.markdown("### 🔀 Prueba de Enrutamiento Inteligente")
        st.caption("Verifica que el router seleccione la herramienta correcta según el contexto")
        
        st.warning(
            "⚠️ **Importante:** Estas preguntas deben hacerse en secuencia para probar el enrutamiento contextual."
        )
        
        for i, faq in enumerate(test_types['routing']):
            with st.container():
                col1, col2, col3 = st.columns([0.3, 3, 1])
                with col1:
                    st.markdown(f"### {faq['icon']}")
                with col2:
                    st.markdown(f"**{i+1}. {faq['question']}**")
                    st.caption(faq['test_purpose'])
                with col3:
                    if st.button("🚀 Probar", key=f"faq_routing_{i}"):
                        st.session_state.pending_question = faq['question']
                        st.session_state.switch_to_chat = True
                        st.rerun()
        st.divider()
    
    # SECCIÓN ADICIONAL: Generar FAQs
    st.markdown("### 🛠️ Herramientas")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Generar FAQs desde documentos**")
        st.caption("Procesa los documentos markdown y crea un archivo JSON estructurado")
    with col2:
        if st.button("🔄 Generar", key="generate_faqs"):
            with st.spinner("Generando FAQs desde documentos..."):
                if generate_faq_json():
                    st.success("✅ FAQs generadas exitosamente")
                    st.session_state.json_generated = True
                else:
                    st.error("❌ Error generando FAQs")

# ============================================================================
# VENTANA 2: ADMINISTRACIÓN
# ============================================================================

def page_admin():
    """Página de administración."""
    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg, #00A651 0%, #008C45 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
        ">
            <h1 style="margin: 0; color: white; font-size: 2rem;">
                ⚙️ Panel de Administración
            </h1>
            <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">
                Configuración y monitoreo del sistema
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab1, tab2 = st.tabs(
        ["⚙️ Configuración", "🔧 Herramientas del Core"]
    )
    
    # TAB 1: CONFIGURACIÓN
    with tab1:
        st.subheader("Configuración de Parámetros")
        
        # MOSTRAR VALORES ACTUALES EN LA PARTE SUPERIOR
        st.info(
            f"📊 **Configuración Activa:**\n\n"
            f"• Proveedor: **{config.llm.provider}** | Modelo: **{config.llm.model}**\n"
            f"• Temperatura: **{config.llm.temperature}** | Top-K: **{config.llm.top_k}** | Max Tokens: **{config.llm.max_tokens}**\n"
            f"• Memoria: **{config.memory.max_tokens} tokens** | Turnos: **{config.memory.max_turns}**\n"
            f"• Streaming: **{'Activo' if config.streaming.enabled else 'Inactivo'}** ({config.streaming.speed_ms}ms)"
        )
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**LLM Settings**")
            
            # Model Selection
            st.markdown("**Proveedor y Modelo**")
            
            # Obtener el índice correcto del proveedor actual
            providers = ["OpenAI", "Google Gemini", "Ollama"]
            current_provider_index = 0
            if "gemini" in config.llm.provider.lower() or "google" in config.llm.provider.lower():
                current_provider_index = 1
            elif "ollama" in config.llm.provider.lower():
                current_provider_index = 2
            
            provider = st.selectbox(
                "Proveedor de LLM",
                options=providers,
                index=current_provider_index
            )
            
            if provider == "OpenAI":
                models = config.get_openai_models()
            elif provider == "Google Gemini":
                models = config.get_google_models()
            else:  # Ollama
                models = config.get_ollama_models()
            
            selected_model = st.selectbox(
                "Modelo",
                options=models,
                index=models.index(config.llm.model) if config.llm.model in models else 0
            )
            
            if selected_model != config.llm.model:
                config.llm.model = selected_model
                config.llm.provider = provider  # Guardar proveedor seleccionado
                # Reinicializar agente con nuevo modelo Y proveedor
                st.session_state.agent = ManuelitaAgent(provider=provider)
                st.success(f"✅ Modelo cambiado a: {selected_model} ({provider})")
                st.rerun()
            
            st.divider()
            
            # Temperature, Top K, Max Tokens
            st.markdown("**Parámetros de Generación**")
            new_temp = st.slider(
                "Temperatura (0.0-1.0)",
                min_value=0.0,
                max_value=1.0,
                value=float(config.llm.temperature),
                step=0.05,
                help="Controla la aleatoriedad: 0=determinista, 1=creativo"
            )
            if new_temp != config.llm.temperature:
                config.llm.temperature = new_temp
                # Actualizar LLM si es posible
                if st.session_state.agent.llm:
                    st.session_state.agent.llm.temperature = new_temp
            
            new_top_k = st.number_input(
                "Top K (documentos RAG)",
                min_value=1,
                max_value=10,
                value=int(config.llm.top_k),
                help="Número de chunks a recuperar del RAG"
            )
            if new_top_k != config.llm.top_k:
                config.llm.top_k = new_top_k
            
            new_max_tokens = st.number_input(
                "Max Tokens (respuesta)",
                min_value=100,
                max_value=2000,
                value=int(config.llm.max_tokens),
                step=100,
                help="Límite de tokens para la respuesta generada"
            )
            if new_max_tokens != config.llm.max_tokens:
                config.llm.max_tokens = new_max_tokens
        
        with col2:
            st.write("**Streaming Settings**")
            config.streaming.enabled = st.checkbox(
                "Streaming Activo",
                value=config.streaming.enabled
            )
            config.streaming.speed_ms = st.slider(
                "Velocidad de Streaming (Delay ms por carácter)",
                min_value=10,
                max_value=200,
                value=config.streaming.speed_ms,
                step=10,
                help="Menor = más rápido, Mayor = más lento. Ej: 10ms rápido, 100ms normal, 200ms lento"
            )
            config.streaming.icon = st.selectbox(
                "Icono de Streaming",
                options=config.get_icon_options(),
                index=config.get_icon_options().index(config.streaming.icon)
            )
        
        st.divider()
        st.write("**Memoria Settings**")
        col1, col2 = st.columns(2)
        with col1:
            new_mem_tokens = st.number_input(
                "Max Tokens Memoria",
                min_value=5000,
                max_value=50000,
                value=int(config.memory.max_tokens),
                step=5000,
                help="Límite de tokens para contexto conversacional"
            )
            if new_mem_tokens != config.memory.max_tokens:
                config.memory.max_tokens = new_mem_tokens
                # Actualizar memoria del agente
                st.session_state.agent.memory.max_tokens = new_mem_tokens
        with col2:
            new_mem_turns = st.number_input(
                "Max Turnos Memoria",
                min_value=10,
                max_value=100,
                value=int(config.memory.max_turns),
                step=5,
                help="Número máximo de intercambios a recordar"
            )
            if new_mem_turns != config.memory.max_turns:
                config.memory.max_turns = new_mem_turns
                st.session_state.agent.memory.max_turns = new_mem_turns
        
        st.success("✅ Configuración actualizada y aplicada al agente")
    
    # TAB 2: HERRAMIENTAS DEL CORE
    with tab2:
        st.subheader("🔧 Arquitectura y Herramientas del Core")
        
        # SECCIÓN 1: MODELO Y CONFIGURACIÓN ACTUAL
        st.markdown("### 🤖 Modelo LLM Activo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Proveedor", config.llm.provider)
        with col2:
            st.metric("Modelo", config.llm.model)
        with col3:
            st.metric("Temperatura", f"{config.llm.temperature}")
        
        st.divider()
        
        # SECCIÓN 2: FLUJO DE PROCESAMIENTO
        st.markdown("### 🔀 Pipeline de Procesamiento")
        st.markdown("""
        ```
        Usuario → Router → [RAG / Structured Tool] → Contexto → LLM → Respuesta
        ```
        """)
        
        stats = st.session_state.agent.get_agent_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Router", "✅ Activo")
        with col2:
            st.metric("RAG", "✅" if stats['rag_available'] else "❌")
        with col3:
            st.metric("Structured", "✅" if stats['structured_tool_available'] else "❌")
        with col4:
            st.metric("LLM", "✅" if stats['llm_available'] else "❌")
        
        st.divider()
        
        # SECCIÓN 3: SISTEMA RAG DETALLADO
        st.markdown("### 📚 Sistema RAG (Retrieval-Augmented Generation)")
        
        if st.session_state.agent.rag:
            rag = st.session_state.agent.rag
            rag_stats = rag.get_stats()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Configuración de Embeddings**")
                st.code(f"Modelo: {rag.embedding_model_name}", language="text")
                st.code(f"Base Vectorial: ChromaDB", language="text")
                st.code(f"Directorio: {rag.vectordb_dir}", language="text")
                
                st.markdown("**Estadísticas de Documentos**")
                st.metric("Total Documentos", rag_stats['total_documents'])
                st.metric("Total Chunks", rag_stats['total_chunks'])
            
            with col2:
                st.markdown("**Estrategia de Búsqueda**")
                st.info(
                    "🔍 **Búsqueda Híbrida**\n\n"
                    "• Vectorial (75%): Semántica con embeddings\n"
                    "• BM25 (25%): Keyword matching\n"
                    "• Re-ranking: CrossEncoder (BAAI/bge-reranker-base)\n"
                    "• Top-K final: 4 chunks"
                )
            
            st.divider()
            
            # VISUALIZAR CHUNKS REALES
            st.markdown("**🔍 Explorar Chunks en la Base Vectorial**")
            
            if rag.splits:
                num_samples = st.slider(
                    "Número de chunks a visualizar",
                    min_value=1,
                    max_value=min(10, len(rag.splits)),
                    value=min(5, len(rag.splits))
                )
                
                st.caption(f"Mostrando {num_samples} de {len(rag.splits)} chunks disponibles")
                
                for i, chunk in enumerate(rag.splits[:num_samples], 1):
                    with st.expander(f"📄 Chunk {i} - {chunk.metadata.get('source', 'Unknown')}"):
                        st.markdown("**Metadata:**")
                        st.json(chunk.metadata)
                        st.markdown("**Contenido:**")
                        st.text_area(
                            "Texto del chunk",
                            value=chunk.page_content,
                            height=200,
                            key=f"chunk_{i}",
                            disabled=True
                        )
            else:
                st.warning("No hay chunks disponibles en la base vectorial")
            
            # TEST DE BÚSQUEDA
            st.divider()
            st.markdown("**🧪 Test de Búsqueda RAG**")
            test_query = st.text_input(
                "Ingresa una consulta para probar el retriever",
                placeholder="Ej: ¿Qué es la política de devoluciones?"
            )
            
            if test_query:
                with st.spinner("Buscando chunks relevantes..."):
                    try:
                        search_result = rag.search(test_query, top_k=config.llm.top_k)
                        
                        # El método search retorna un dict con 'documents' como lista
                        documents = search_result.get('documents', [])
                        context = search_result.get('context', '')
                        
                        if documents:
                            st.success(f"✅ {len(documents)} chunks recuperados")
                            
                            # Mostrar contexto consolidado
                            with st.expander("📖 Contexto Consolidado (lo que ve el LLM)"):
                                st.text_area(
                                    "Contexto completo",
                                    value=context,
                                    height=200,
                                    disabled=True
                                )
                            
                            st.divider()
                            st.markdown("**Documentos Individuales:**")
                            
                            for idx, doc in enumerate(documents, 1):
                                with st.expander(
                                    f"🎯 Resultado {idx} - {doc.get('relevance', 'N/A')} | Rank: {doc.get('rank', idx)}"
                                ):
                                    st.markdown(f"**Fuente:** `{doc.get('source', 'Unknown')}`")
                                    st.markdown(f"**Relevancia:** {doc.get('relevance', 'N/A')}")
                                    st.markdown(f"**Contenido (preview):**")
                                    st.write(doc.get('content', 'Sin contenido'))
                        else:
                            st.warning("⚠️ No se encontraron resultados para esta consulta")
                    except Exception as e:
                        st.error(f"❌ Error en búsqueda: {str(e)}")
                        logger.error(f"Error en test de búsqueda RAG: {e}")
        else:
            st.warning("❌ Sistema RAG no disponible")
        
        st.divider()
        
        # SECCIÓN 4: HERRAMIENTA ESTRUCTURADA
        st.markdown("### 📊 Herramienta de Datos Estructurados")
        
        if st.session_state.agent.structured_tool:
            structured = st.session_state.agent.structured_tool
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Consultas Disponibles**")
                queries = structured.get_available_queries()
                for query in queries:
                    st.code(f"• {query}", language="text")
            
            with col2:
                st.markdown("**Características**")
                st.info(
                    "• Respuestas estructuradas en JSON\n"
                    "• Búsqueda exacta por palabras clave\n"
                    "• Ideal para FAQs y datos tabulares\n"
                    "• Sin necesidad de embeddings"
                )
        else:
            st.warning("❌ Herramienta estructurada no disponible")
        
        st.divider()
        
        # SECCIÓN 5: CONEXIÓN CON VENTANA CHAT
        st.markdown("### 💬 Integración con Ventana de Chat")
        st.info(
            "**Flujo de Interacción:**\n\n"
            "1. Usuario escribe pregunta en Chat\n"
            "2. Router analiza la pregunta y selecciona herramienta (RAG/Structured)\n"
            "3. Herramienta recupera contexto relevante\n"
            "4. LLM genera respuesta usando el contexto\n"
            "5. Respuesta se muestra en Chat con streaming\n"
            "6. Interacción se guarda en memoria de conversación\n\n"
            "**Memoria:** FIFO con límite de 20K tokens por conversación"
        )
        
        # VISUALIZAR ESTADO ACTUAL
        st.markdown("**Estado de Conversaciones Activas**")
        session_stats = st.session_state.session_manager.get_session_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conversaciones Activas", session_stats['total_conversations'])
        with col2:
            st.metric("Turnos Totales", session_stats['total_turns_in_session'])

# ============================================================================
# VENTANA 3: CHAT INTERACTIVO
# ============================================================================

def page_chat():
    """Página de chat interactivo."""
    
    # VALIDAR API KEY
    import os
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
    has_google_key = bool(os.getenv("GOOGLE_API_KEY"))
    
    if not has_openai_key and not has_google_key:
        st.error(
            "❌ **No hay API Keys configuradas**\n\n"
            "Para usar el chat, necesitas configurar una API key. "
            "Ver: CHAT_TROUBLESHOOTING.md para instrucciones."
        )
        st.info(
            "**Opciones:**\n"
            "1. Crea archivo `.env` con OPENAI_API_KEY o GOOGLE_API_KEY\n"
            "2. O configura variables de entorno: `$env:OPENAI_API_KEY = 'tu-key'`\n"
            "3. Reinicia Streamlit después de configurar"
        )
        return
    
    if not st.session_state.agent.llm:
        st.warning(
            "⚠️ **LLM no inicializado**\n\n"
            "El modelo LLM no se pudo cargar. Verifica que:\n"
            "- Tengas `langchain-openai` o `langchain-google-genai` instalado\n"
            "- Tu API key sea válida\n"
            "- Reinicia la aplicación si acabas de configurar la API key"
        )
    
    # SIDEBAR
    with st.sidebar:
        st.header("💬 Conversaciones")
        
        # Crear nueva conversación
        if st.button("➕ Nueva Conversación"):
            conv_name = f"Conversación {len(st.session_state.session_manager.conversations) + 1}"
            st.session_state.session_manager.create_conversation(conv_name)
            st.session_state.current_conversation = conv_name
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        
        # Listar conversaciones
        conversations = st.session_state.session_manager.list_conversations()
        for conv_id in conversations:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(conv_id, key=f"conv_{conv_id}"):
                    st.session_state.current_conversation = conv_id
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv_id}"):
                    st.session_state.session_manager.delete_conversation(conv_id)
                    st.rerun()
        
        st.divider()
        
        # Stats
        session_stats = st.session_state.session_manager.get_session_stats()
        st.metric("Conversaciones", session_stats['total_conversations'])
        st.metric("Turnos Totales", session_stats['total_turns_in_session'])
    
    # CHAT PRINCIPAL
    st.header(f"💬 {st.session_state.current_conversation}")
    
    # Obtener memoria de la conversación actual
    current_conv_memory = st.session_state.session_manager.get_conversation(
        st.session_state.current_conversation
    )
    
    if current_conv_memory is None:
        st.error("❌ Conversación no encontrada. Por favor, selecciona una conversación válida.")
        return
    
    # Mostrar historial de la conversación actual
    turns = current_conv_memory.get_all_turns()
    
    # MENSAJE DE BIENVENIDA (solo si no hay historial)
    if not turns:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #00A651 0%, #008C45 100%);
                padding: 2rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0, 166, 81, 0.1);
            ">
                <div style="text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 3rem;">🌿</h1>
                    <h2 style="margin: 0.5rem 0; color: white; font-weight: 600;">Bienvenido a Manuelita Insight</h2>
                    <p style="margin: 0.5rem 0; font-size: 1.1rem; opacity: 0.95;">
                        Tu asistente inteligente para conocer más de 160 años de historia
                    </p>
                    <p style="margin: 1rem 0 0 0; font-size: 0.95rem; opacity: 0.9;">
                        🌱 Azúcar • ⚡ Bioenergía • 🦐 Acuicultura • 🍇 Frutas
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    for turn in turns:
        with st.chat_message("user"):
            st.write(turn.user_question)
        
        with st.chat_message("assistant"):
            st.write(turn.bot_response)
            if turn.sources:
                st.caption(f"📚 Fuentes: {', '.join(turn.sources)}")
    
    # Verificar si hay una pregunta pendiente desde FAQs
    if st.session_state.pending_question:
        user_input = st.session_state.pending_question
        st.session_state.pending_question = None  # Limpiar
    else:
        # Input del usuario
        user_input = st.chat_input("Escribe tu pregunta...")
    
    if user_input:
        # Mostrar pregunta
        with st.chat_message("user"):
            st.write(user_input)
        
        # Procesar
        with st.chat_message("assistant"):
            with st.spinner("Procesando..."):
                # Pasar contexto de memoria de la conversación actual
                memory_ctx = current_conv_memory.get_conversation_context()
                result = process_user_input(user_input, memory_context=memory_ctx)
            
            # Guardar en la memoria de la conversación actual
            if result['success']:
                current_conv_memory.add_turn(
                    user_question=user_input,
                    bot_response=result['answer'],
                    rag_context=result.get('context_used', ''),
                    sources=result.get('sources', []),
                    tool_used=result.get('tool_used', 'unknown')
                )
            
            if config.streaming.enabled and result['success']:
                stream_response(result['answer'], speed_ms=config.streaming.speed_ms)
            else:
                st.write(result['answer'])
            
            if result.get('sources'):
                st.caption(f"📚 {result['tool_used'].upper()}: {', '.join(result['sources'])}")

# ============================================================================
# NAVEGACIÓN PRINCIPAL
# ============================================================================

# Navegación con estilo corporativo
st.sidebar.markdown(
    """
    <div style="
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 3px solid #00A651;
    ">
        <h2 style="
            margin: 0;
            color: #00A651;
            font-size: 1.5rem;
            font-weight: 700;
        ">
            🏠 Navegación
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

# Cambiar a Chat si hay switch pendiente desde FAQs
if st.session_state.switch_to_chat:
    default_page = 0  # índice de Chat
    st.session_state.switch_to_chat = False
else:
    default_page = 0  # Chat por defecto

st.sidebar.markdown(
    "<p style='font-weight: 600; color: #3D5A4C; margin-bottom: 0.5rem;'>Selecciona una sección:</p>",
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "Selecciona una sección:",
    ["💬 Chat", "⚙️ Admin", "❓ FAQs"],
    index=default_page,
    label_visibility="collapsed"
)

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #00A651 0%, #008C45 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
    ">
        <h3 style="margin: 0; color: white; font-size: 1.2rem;">🌿 Manuelita</h3>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.95;">
            <strong>Asistente Inteligente</strong><br>
            160+ años generando valor sostenible
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Ejecutar página
if page == "💬 Chat":
    page_chat()
elif page == "⚙️ Admin":
    page_admin()
elif page == "❓ FAQs":
    page_faqs()

# ============================================================================
# FOOTER
# ============================================================================

st.sidebar.divider()
st.sidebar.caption(
    "🔧 Powered by LangChain + Streamlit\n"
    "Memory: FIFO (20K tokens) | RAG: Hybrid Search + Reranking"
)
