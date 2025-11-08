"""
Aplicación Streamlit - Asistente Inteligente Manuelita

3 Ventanas: FAQs, Admin, Chat Interactivo
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List
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
    page_title="Manuelita Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    """Página de FAQs autogeneradas."""
    st.header("❓ Preguntas Frecuentes")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("Ejemplo de Consultas por Tipo")
    
    with col2:
        if st.button("🔄 Generar FAQs"):
            with st.spinner("Generando FAQs desde documentos..."):
                if generate_faq_json():
                    st.success("✅ FAQs generadas exitosamente")
                    st.session_state.json_generated = True
                else:
                    st.error("❌ Error generando FAQs")
    
    # Mostrar FAQs
    for i, faq in enumerate(SAMPLE_FAQS, 1):
        with st.container():
            col1, col2, col3 = st.columns([0.5, 3, 1.5])
            
            with col1:
                if faq['type'] == 'rag':
                    st.write("📚")
                elif faq['type'] == 'memory':
                    st.write("🧠")
                elif faq['type'] == 'structured':
                    st.write("📊")
                else:
                    st.write("🔀")
            
            with col2:
                st.write(f"**{faq['question']}**")
                st.caption(faq['description'])
            
            with col3:
                if st.button("Preguntar", key=f"faq_{i}"):
                    st.session_state.user_input = faq['question']
                    st.rerun()
    
    st.divider()
    st.info("💡 Selecciona una pregunta o escribe la tuya en la ventana de Chat")

# ============================================================================
# VENTANA 2: ADMINISTRACIÓN
# ============================================================================

def page_admin():
    """Página de administración."""
    st.header("⚙️ Panel de Administración")
    
    tab1, tab2, tab3, tab4 = st.tabs(
        ["⚙️ Configuración", "📊 Estadísticas", "📋 Historial", "🔧 Herramientas"]
    )
    
    # TAB 1: CONFIGURACIÓN
    with tab1:
        st.subheader("Configuración de Parámetros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**LLM Settings**")
            
            # Model Selection
            st.markdown("**Proveedor y Modelo**")
            provider = st.selectbox(
                "Proveedor de LLM",
                options=["OpenAI", "Google Gemini", "Ollama"],
                index=0
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
            config.llm.temperature = st.slider(
                "Temperatura (0.0-1.0)",
                min_value=0.0,
                max_value=1.0,
                value=config.llm.temperature,
                step=0.05
            )
            config.llm.top_k = st.number_input(
                "Top K (documentos RAG)",
                min_value=1,
                max_value=10,
                value=config.llm.top_k
            )
            config.llm.max_tokens = st.number_input(
                "Max Tokens (respuesta)",
                min_value=100,
                max_value=2000,
                value=config.llm.max_tokens,
                step=100
            )
        
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
            config.memory.max_tokens = st.number_input(
                "Max Tokens Memoria",
                min_value=5000,
                max_value=50000,
                value=config.memory.max_tokens,
                step=5000
            )
        with col2:
            config.memory.max_turns = st.number_input(
                "Max Turnos Memoria",
                min_value=10,
                max_value=100,
                value=config.memory.max_turns,
                step=5
            )
        
        st.success("✅ Configuración actualizada")
    
    # TAB 2: ESTADÍSTICAS
    with tab2:
        st.subheader("Estadísticas del Agente")
        
        stats = st.session_state.agent.get_agent_stats()
        
        # Mostrar modelo actual
        st.info(f"🤖 **Modelo Actual:** {config.llm.model}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("RAG", "✅" if stats['rag_available'] else "❌")
        with col2:
            st.metric("Structured", "✅" if stats['structured_tool_available'] else "❌")
        with col3:
            st.metric("LLM", "✅" if stats['llm_available'] else "❌")
        with col4:
            st.metric("Ollama", "✅" if stats['use_ollama'] else "❌")
        
        st.divider()
        st.write("**Memoria Actual**")
        memory_stats = stats['memory_stats']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Turnos", memory_stats['total_turns'])
        with col2:
            st.metric("Tokens", f"{memory_stats['total_tokens']}/{memory_stats['max_tokens']}")
        with col3:
            st.metric("Uso %", f"{memory_stats['token_usage_percent']:.1f}%")
        
        st.write("**Uso por Herramienta**")
        tool_usage = memory_stats.get('tool_usage', {})
        if tool_usage:
            st.bar_chart(tool_usage)
        else:
            st.info("Sin historial aún")
    
    # TAB 3: HISTORIAL
    with tab3:
        st.subheader("Historial de Interacciones")
        
        memory = st.session_state.agent.memory
        turns = memory.get_all_turns()
        
        if turns:
            for turn in turns[-10:]:  # Últimas 10
                with st.expander(f"Turno {turn.turn_id}: {turn.user_question[:50]}..."):
                    st.write(f"**Q:** {turn.user_question}")
                    st.write(f"**A:** {turn.bot_response}")
                    st.caption(f"Tool: {turn.tool_used} | Fuentes: {', '.join(turn.sources)}")
                    st.caption(f"Timestamp: {datetime.fromtimestamp(turn.timestamp)}")
        else:
            st.info("Sin historial aún")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Exportar Historial"):
                json_data = json.dumps(
                    [t.to_dict() for t in turns],
                    indent=2,
                    default=str
                )
                st.download_button(
                    label="Descargar JSON",
                    data=json_data,
                    file_name=f"historial_{datetime.now().isoformat()}.json"
                )
        
        with col2:
            if st.button("🗑️ Limpiar Historial"):
                memory.reset()
                st.rerun()
    
    # TAB 4: HERRAMIENTAS
    with tab4:
        st.subheader("Información de Herramientas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Sistema RAG**")
            if st.session_state.agent.rag:
                rag_stats = st.session_state.agent.rag.get_stats()
                st.json(rag_stats)
            else:
                st.warning("RAG no disponible")
        
        with col2:
            st.write("**Herramienta Estructurada**")
            if st.session_state.agent.structured_tool:
                st.json({
                    'available_queries': st.session_state.agent.structured_tool.get_available_queries()
                })
            else:
                st.warning("Structured Tool no disponible")

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
    
    for turn in turns:
        with st.chat_message("user"):
            st.write(turn.user_question)
        
        with st.chat_message("assistant"):
            st.write(turn.bot_response)
            if turn.sources:
                st.caption(f"📚 Fuentes: {', '.join(turn.sources)}")
    
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

st.sidebar.title("🏠 Navegación")
page = st.sidebar.radio(
    "Selecciona una sección:",
    ["❓ FAQs", "⚙️ Admin", "💬 Chat"]
)

st.sidebar.divider()
st.sidebar.info(
    "📌 **Asistente Inteligente Manuelita**\n"
    "Versión 1.0 - Memoria conversacional con enrutamiento RAG/Structured"
)

# Ejecutar página
if page == "❓ FAQs":
    page_faqs()
elif page == "⚙️ Admin":
    page_admin()
elif page == "💬 Chat":
    page_chat()

# ============================================================================
# FOOTER
# ============================================================================

st.sidebar.divider()
st.sidebar.caption(
    "🔧 Powered by LangChain + Streamlit\n"
    "Memory: FIFO (20K tokens) | RAG: Hybrid Search + Reranking"
)
