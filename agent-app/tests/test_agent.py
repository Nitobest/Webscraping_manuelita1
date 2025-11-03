"""
Tests para el Agente Inteligente

Valida: Memoria, Enrutamiento, Herramientas, RAG
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import ConversationMemory, SessionManager
from tools.structured_tool import is_structured_question
from config import config


class TestMemory:
    """Tests para el gestor de memoria."""
    
    def test_memory_creation(self):
        """Crear memoria correctamente."""
        memory = ConversationMemory(max_tokens=5000)
        assert memory.max_tokens == 5000
        assert len(memory.turns) == 0
        assert memory.total_tokens == 0
    
    def test_add_turn(self):
        """Añadir turno a la memoria."""
        memory = ConversationMemory()
        turn = memory.add_turn(
            user_question="¿Quién eres?",
            bot_response="Soy un asistente.",
            sources=["test.md"]
        )
        assert turn.turn_id == 0
        assert len(memory.turns) == 1
        assert memory.total_tokens > 0
    
    def test_memory_fifo(self):
        """Verificar que FIFO funciona correctamente."""
        memory = ConversationMemory(max_tokens=500, max_turns=3)
        
        for i in range(5):
            memory.add_turn(
                user_question=f"Pregunta {i}",
                bot_response=f"Respuesta {i}" * 50  # Contenido largo
            )
        
        # Solo debe haber máximo 3 turnos
        assert len(memory.turns) <= 3
    
    def test_memory_stats(self):
        """Obtener estadísticas de memoria."""
        memory = ConversationMemory()
        memory.add_turn(
            user_question="Q1",
            bot_response="R1",
            tool_used="rag"
        )
        memory.add_turn(
            user_question="Q2",
            bot_response="R2",
            tool_used="structured"
        )
        
        stats = memory.get_stats()
        assert stats['total_turns'] == 2
        assert 'rag' in stats['tool_usage']
        assert 'structured' in stats['tool_usage']


class TestSessionManager:
    """Tests para el gestor de sesión."""
    
    def test_create_conversation(self):
        """Crear conversación."""
        manager = SessionManager()
        conv = manager.create_conversation("conv_1")
        
        assert conv is not None
        assert manager.current_conversation_id == "conv_1"
        assert len(manager.conversations) == 1
    
    def test_switch_conversation(self):
        """Cambiar entre conversaciones."""
        manager = SessionManager()
        manager.create_conversation("conv_1")
        manager.create_conversation("conv_2")
        
        success = manager.switch_conversation("conv_2")
        assert success
        assert manager.current_conversation_id == "conv_2"
    
    def test_delete_conversation(self):
        """Eliminar conversación."""
        manager = SessionManager()
        manager.create_conversation("conv_1")
        manager.create_conversation("conv_2")
        
        success = manager.delete_conversation("conv_1")
        assert success
        assert len(manager.conversations) == 1


class TestRouting:
    """Tests para enrutamiento de preguntas."""
    
    def test_structured_questions(self):
        """Detectar preguntas para Structured Tool."""
        questions = [
            "¿Cuál es el teléfono?",
            "¿Dónde están ubicados?",
            "¿Qué horarios tienen?",
            "¿Cuál es el email?"
        ]
        
        for q in questions:
            assert is_structured_question(q), f"No detectó: {q}"
    
    def test_rag_questions(self):
        """Detectar preguntas para RAG."""
        questions = [
            "¿Cuál es la historia de la empresa?",
            "¿Qué productos fabrican?",
            "¿Cómo es su modelo de sostenibilidad?"
        ]
        
        for q in questions:
            assert not is_structured_question(q), f"Incorrecto: {q}"


class TestConfiguration:
    """Tests para configuración."""
    
    def test_config_defaults(self):
        """Verificar valores por defecto."""
        assert config.llm.temperature == 0.05
        assert config.streaming.speed_ms == 50
        assert config.memory.max_tokens == 20000
    
    def test_streaming_icons(self):
        """Verificar iconos disponibles."""
        icons = config.get_icon_options()
        assert len(icons) >= 11
        assert '🐢' in icons
        assert '🚀' in icons
    
    def test_config_dict_conversion(self):
        """Convertir config a diccionario."""
        config_dict = config.to_dict()
        assert 'llm' in config_dict
        assert 'streaming' in config_dict
        assert 'memory' in config_dict


class TestIntegration:
    """Tests de integración."""
    
    def test_full_conversation_flow(self):
        """Flujo completo de conversación."""
        memory = ConversationMemory()
        
        # Simular conversación
        turn1 = memory.add_turn(
            user_question="¿Cuál es la historia?",
            bot_response="Manuelita fue fundada en 1864...",
            tool_used="rag",
            sources=["history.md"]
        )
        
        turn2 = memory.add_turn(
            user_question="¿Y cuántas sedes tienen?",
            bot_response="Tienen sedes en varios países...",
            tool_used="rag",
            sources=["contacts.md"]
        )
        
        # Validar flujo
        assert len(memory.turns) == 2
        assert memory.turns[0].turn_id == 0
        assert memory.turns[1].turn_id == 1
        
        # Verificar contexto
        context = memory.get_conversation_context()
        assert "historia" in context.lower()
        assert "sedes" in context.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
