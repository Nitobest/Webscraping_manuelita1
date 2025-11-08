"""
Configuración Centralizada del Agente

Parámetros de LLM, streaming, memoria, etc.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import os

try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except ImportError:
    # Si dotenv no está instalado, ignorar
    pass


@dataclass
class LLMConfig:
    """Configuración del modelo LLM."""
    model: str = "gpt-3.5-turbo"
    provider: str = "OpenAI"  # OpenAI, Google Gemini, o Ollama
    temperature: float = 0.05
    top_k: int = 4
    max_tokens: int = 500
    use_ollama: bool = False
    ollama_model: str = "qwen3:4b"
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Opciones disponibles de modelos
    OPENAI_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "o1",
        "o1-mini"
    ]
    
    GOOGLE_MODELS = [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]
    
    OLLAMA_MODELS = [
        "qwen3:4b",
        "deepseek-r1:8b",
        "gemma3:12b",
        "nomic-embed-text:latest"
    ]


@dataclass
class StreamingConfig:
    """Configuración del streaming."""
    enabled: bool = True
    speed_ms: int = 10  # milisegundos por carácter
    icon: str = "✨"  # Ícono por defecto
    
    # Iconos disponibles
    ICONS = {
        'tortuga': '🐢',
        'rayo': '⚡',
        'cohete': '🚀',
        'reloj': '⏱️',
        'vapor': '💨',
        'fuego': '🔥',
        'chispa': '✨',
        'onda': '🌊',
        'objetivo': '🎯',
        'estrella': '⭐',
        'brujula': '🎨',
        'destello': '🌟'
    }


@dataclass
class MemoryConfig:
    """Configuración de memoria."""
    max_tokens: int = 20000
    max_turns: int = 50
    fifo_enabled: bool = True


@dataclass
class UIConfig:
    """Configuración de interfaz."""
    title: str = "Asistente Inteligente Manuelita"
    faq_max_questions: int = 4
    sidebar_width: int = 300
    chat_height: int = 600


@dataclass
class LangSmithConfig:
    """Configuración de LangSmith (Observabilidad)."""
    enabled: bool = False
    api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    project_name: str = os.getenv("LANGCHAIN_PROJECT", "manuelita-agent")
    endpoint: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    def __post_init__(self):
        """Verifica si está habilitado basado en variables de entorno."""
        tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower()
        self.enabled = tracing in ["true", "1", "yes"]


class AppConfig:
    """Configuración global de la aplicación."""
    
    def __init__(self):
        self.llm = LLMConfig()
        self.streaming = StreamingConfig()
        self.memory = MemoryConfig()
        self.ui = UIConfig()
        self.langsmith = LangSmithConfig()
        self.data_dir = "../data/raw/processed"
        self.vectordb_dir = "./vectordb"
        self.structured_data_file = "tools/data/faq_structured.json"
    
    @staticmethod
    def get_icon_options() -> List[str]:
        """Retorna lista de iconos disponibles."""
        return [v for v in StreamingConfig.ICONS.values()]
    
    @staticmethod
    def get_icon_name_by_value(icon: str) -> str:
        """Obtiene el nombre del icono por su valor."""
        for name, val in StreamingConfig.ICONS.items():
            if val == icon:
                return name
        return "unknown"
    
    @staticmethod
    def get_openai_models() -> List[str]:
        """Retorna lista de modelos OpenAI disponibles."""
        return LLMConfig.OPENAI_MODELS
    
    @staticmethod
    def get_google_models() -> List[str]:
        """Retorna lista de modelos Google Gemini disponibles."""
        return LLMConfig.GOOGLE_MODELS
    
    @staticmethod
    def get_ollama_models() -> List[str]:
        """Retorna lista de modelos Ollama disponibles."""
        return LLMConfig.OLLAMA_MODELS
    
    @staticmethod
    def get_all_models() -> Dict[str, List[str]]:
        """Retorna todos los modelos disponibles organizados por proveedor."""
        return {
            'OpenAI': LLMConfig.OPENAI_MODELS,
            'Google Gemini': LLMConfig.GOOGLE_MODELS,
            'Ollama (Local)': LLMConfig.OLLAMA_MODELS
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte configuración a diccionario."""
        return {
            'llm': {
                'model': self.llm.model,
                'temperature': self.llm.temperature,
                'top_k': self.llm.top_k,
                'max_tokens': self.llm.max_tokens,
                'use_ollama': self.llm.use_ollama,
                'ollama_model': self.llm.ollama_model,
                'api_key_configured': bool(self.llm.api_key)
            },
            'streaming': {
                'enabled': self.streaming.enabled,
                'speed_ms': self.streaming.speed_ms,
                'icon': self.streaming.icon,
                'available_icons': self.get_icon_options()
            },
            'memory': {
                'max_tokens': self.memory.max_tokens,
                'max_turns': self.memory.max_turns,
                'fifo_enabled': self.memory.fifo_enabled
            },
            'ui': {
                'title': self.ui.title,
                'faq_max_questions': self.ui.faq_max_questions,
                'sidebar_width': self.ui.sidebar_width,
                'chat_height': self.ui.chat_height
            },
            'langsmith': {
                'enabled': self.langsmith.enabled,
                'project_name': self.langsmith.project_name,
                'api_key_configured': bool(self.langsmith.api_key),
                'endpoint': self.langsmith.endpoint
            }
        }


# Instancia global
config = AppConfig()


# FAQs optimizadas para probar el sistema
SAMPLE_FAQS = [
    {
        "type": "rag",
        "icon": "📚",
        "question": "¿Cuál es la historia de Manuelita?",
        "description": "Prueba de RAG: Pregunta general respondida desde documentos",
        "test_purpose": "Verifica que el sistema recupere información de la base vectorial"
    },
    {
        "type": "structured",
        "icon": "📊",
        "question": "¿Cuál es el horario de atención?",
        "description": "Prueba de Herramienta Estructurada: Dato directo de FAQ",
        "test_purpose": "Verifica que el router seleccione la herramienta estructurada"
    },
    {
        "type": "memory",
        "icon": "🧠",
        "question": "Me llamo Esteban, ¿me puedes ayudar?",
        "description": "Prueba de Memoria: Presentación personal",
        "test_purpose": "Verifica que el sistema almacene información personal"
    },
    {
        "type": "memory",
        "icon": "🧠",
        "question": "¿Recuerdas mi nombre?",
        "description": "Prueba de Memoria: Pregunta de seguimiento",
        "test_purpose": "Verifica que el sistema recuerde información de turnos anteriores"
    },
    {
        "type": "routing",
        "icon": "🔀",
        "question": "¿Qué productos de azúcar ofrecen?",
        "description": "Prueba de Enrutamiento: Combina RAG + contexto",
        "test_purpose": "Verifica que el router seleccione RAG para preguntas específicas"
    },
    {
        "type": "routing",
        "icon": "🔀",
        "question": "¿Y cuál es el precio?",
        "description": "Prueba de Enrutamiento: Pregunta contextual de seguimiento",
        "test_purpose": "Verifica que el sistema use memoria para entender contexto"
    }
]


if __name__ == '__main__':
    # Test config
    print("Configuración cargada:")
    print(f"LLM Model: {config.llm.model}")
    print(f"Streaming Speed: {config.streaming.speed_ms}ms")
    print(f"Iconos disponibles: {config.get_icon_options()}")
    print(f"\nConfiguration dict:")
    import json
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
