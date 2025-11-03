"""
Configuración Centralizada del Agente

Parámetros de LLM, streaming, memoria, etc.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv('.env')


@dataclass
class LLMConfig:
    """Configuración del modelo LLM."""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.05
    top_k: int = 4
    max_tokens: int = 500
    use_ollama: bool = False
    ollama_model: str = "qwen:4b"
    api_key: str = os.getenv("OPENAI_API_KEY", "")


@dataclass
class StreamingConfig:
    """Configuración del streaming."""
    enabled: bool = True
    speed_ms: int = 50  # milisegundos por carácter
    icon: str = "🐢"  # Ícono por defecto
    
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


class AppConfig:
    """Configuración global de la aplicación."""
    
    def __init__(self):
        self.llm = LLMConfig()
        self.streaming = StreamingConfig()
        self.memory = MemoryConfig()
        self.ui = UIConfig()
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
            }
        }


# Instancia global
config = AppConfig()


# Ejemplo de FAQs autogeneradas (estructura)
SAMPLE_FAQS = [
    {
        "type": "rag",
        "question": "¿Cuál es la historia de Manuelita?",
        "description": "Pregunta sobre los orígenes y evolución de la empresa"
    },
    {
        "type": "memory",
        "question": "¿Cuántas sedes tienen en total?",
        "description": "Pregunta de seguimiento que requiere contexto previo"
    },
    {
        "type": "structured",
        "question": "¿Cuál es el número de teléfono de contacto?",
        "description": "Pregunta de dato concreto"
    },
    {
        "type": "routing",
        "question": "¿Dónde puedo comprar sus productos?",
        "description": "Pregunta que puede requerir múltiples herramientas"
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
