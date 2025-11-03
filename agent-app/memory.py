"""
Gestor de Memoria Conversacional (FIFO)

Almacena historial de conversaciones con límite de tokens.
Estructura: pregunta + respuesta + contexto RAG + timestamp + fuentes.
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Representa un turno de conversación."""
    turn_id: int
    user_question: str
    bot_response: str
    rag_context: Optional[str] = None
    sources: List[str] = None
    timestamp: float = None
    tool_used: str = "rag"  # "rag" o "structured"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.sources is None:
            self.sources = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)
    
    def get_token_count(self, model: str = "gpt-3.5-turbo") -> int:
        """Estima el conteo de tokens."""
        # Aproximación simple: 1 token ≈ 4 caracteres
        text = f"{self.user_question} {self.bot_response} {self.rag_context or ''}"
        return len(text) // 4


class ConversationMemory:
    """Gestor de memoria conversacional con FIFO y límite de tokens."""
    
    def __init__(self, max_tokens: int = 20000, max_turns: int = 50):
        """
        Inicializa el gestor de memoria.
        
        Args:
            max_tokens: Límite máximo de tokens en el historial
            max_turns: Límite máximo de turnos (backup)
        """
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []
        self.current_turn_id = 0
        self.total_tokens = 0
    
    def add_turn(self, user_question: str, bot_response: str,
                 rag_context: Optional[str] = None, sources: List[str] = None,
                 tool_used: str = "rag") -> ConversationTurn:
        """
        Añade un turno de conversación.
        
        Args:
            user_question: Pregunta del usuario
            bot_response: Respuesta del bot
            rag_context: Contexto recuperado por RAG (opcional)
            sources: Lista de documentos fuente (opcional)
            tool_used: Herramienta utilizada ("rag" o "structured")
        
        Returns:
            ConversationTurn creado
        """
        turn = ConversationTurn(
            turn_id=self.current_turn_id,
            user_question=user_question,
            bot_response=bot_response,
            rag_context=rag_context,
            sources=sources or [],
            tool_used=tool_used
        )
        
        # Calcular tokens
        turn_tokens = turn.get_token_count()
        
        # Aplicar FIFO si se excede el límite
        while (self.total_tokens + turn_tokens > self.max_tokens or
               len(self.turns) >= self.max_turns) and self.turns:
            removed_turn = self.turns.pop(0)
            self.total_tokens -= removed_turn.get_token_count()
            logger.info(f"Removido turno {removed_turn.turn_id} (FIFO). "
                       f"Tokens: {self.total_tokens}/{self.max_tokens}")
        
        # Añadir el nuevo turno
        self.turns.append(turn)
        self.total_tokens += turn_tokens
        self.current_turn_id += 1
        
        logger.info(f"Turno {turn.turn_id} añadido. Tokens: {self.total_tokens}/{self.max_tokens}")
        return turn
    
    def get_conversation_context(self) -> str:
        """
        Retorna el contexto de conversación formateado para el prompt.
        """
        if not self.turns:
            return "No hay historial de conversación previo."
        
        context_lines = []
        for turn in self.turns:
            context_lines.append(f"**Usuario (Turno {turn.turn_id}):** {turn.user_question}")
            context_lines.append(f"**Asistente:** {turn.bot_response}")
            if turn.sources:
                context_lines.append(f"**Fuentes:** {', '.join(turn.sources)}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def get_last_n_turns(self, n: int = 5) -> List[ConversationTurn]:
        """Retorna los últimos N turnos."""
        return self.turns[-n:] if self.turns else []
    
    def get_all_turns(self) -> List[ConversationTurn]:
        """Retorna todos los turnos."""
        return self.turns.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de la memoria."""
        tool_usage = {}
        for turn in self.turns:
            tool_usage[turn.tool_used] = tool_usage.get(turn.tool_used, 0) + 1
        
        return {
            'total_turns': len(self.turns),
            'total_tokens': self.total_tokens,
            'max_tokens': self.max_tokens,
            'token_usage_percent': (self.total_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            'tool_usage': tool_usage,
            'first_turn': self.turns[0].timestamp if self.turns else None,
            'last_turn': self.turns[-1].timestamp if self.turns else None,
            'conversation_duration_seconds': (self.turns[-1].timestamp - self.turns[0].timestamp) if len(self.turns) > 1 else 0
        }
    
    def reset(self) -> None:
        """Resetea la memoria completamente."""
        self.turns = []
        self.total_tokens = 0
        self.current_turn_id = 0
        logger.info("Memoria reseteada.")
    
    def export_to_json(self, filepath: str) -> bool:
        """Exporta el historial a JSON."""
        try:
            data = {
                'exported_at': datetime.now().isoformat(),
                'turns': [turn.to_dict() for turn in self.turns],
                'stats': self.get_stats()
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Historial exportado a {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exportando historial: {e}")
            return False
    
    def import_from_json(self, filepath: str) -> bool:
        """Importa historial desde JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.turns = []
            self.total_tokens = 0
            self.current_turn_id = 0
            
            for turn_data in data.get('turns', []):
                turn = ConversationTurn(**turn_data)
                self.turns.append(turn)
                self.total_tokens += turn.get_token_count()
                self.current_turn_id = max(self.current_turn_id, turn.turn_id + 1)
            
            logger.info(f"Historial importado desde {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error importando historial: {e}")
            return False


class SessionManager:
    """Gestor de múltiples conversaciones en una sesión."""
    
    def __init__(self):
        """Inicializa el gestor de sesión."""
        self.conversations: Dict[str, ConversationMemory] = {}
        self.current_conversation_id: Optional[str] = None
    
    def create_conversation(self, conversation_id: str) -> ConversationMemory:
        """Crea una nueva conversación."""
        if conversation_id in self.conversations:
            logger.warning(f"Conversación {conversation_id} ya existe.")
            return self.conversations[conversation_id]
        
        self.conversations[conversation_id] = ConversationMemory()
        self.current_conversation_id = conversation_id
        logger.info(f"Conversación '{conversation_id}' creada.")
        return self.conversations[conversation_id]
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """Obtiene una conversación existente."""
        return self.conversations.get(conversation_id)
    
    def switch_conversation(self, conversation_id: str) -> bool:
        """Cambia a una conversación existente."""
        if conversation_id in self.conversations:
            self.current_conversation_id = conversation_id
            logger.info(f"Cambiado a conversación '{conversation_id}'.")
            return True
        logger.warning(f"Conversación '{conversation_id}' no existe.")
        return False
    
    def get_current_conversation(self) -> Optional[ConversationMemory]:
        """Obtiene la conversación actual."""
        if self.current_conversation_id:
            return self.conversations.get(self.current_conversation_id)
        return None
    
    def list_conversations(self) -> Dict[str, Dict[str, Any]]:
        """Lista todas las conversaciones con estadísticas."""
        return {
            conv_id: conv.get_stats()
            for conv_id, conv in self.conversations.items()
        }
    
    def reset_current_conversation(self) -> None:
        """Resetea la conversación actual."""
        if self.current_conversation_id:
            self.conversations[self.current_conversation_id].reset()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Elimina una conversación."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            if self.current_conversation_id == conversation_id:
                self.current_conversation_id = None
            logger.info(f"Conversación '{conversation_id}' eliminada.")
            return True
        return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de toda la sesión."""
        total_turns = sum(
            len(conv.turns) for conv in self.conversations.values()
        )
        total_tokens = sum(
            conv.total_tokens for conv in self.conversations.values()
        )
        
        return {
            'total_conversations': len(self.conversations),
            'current_conversation_id': self.current_conversation_id,
            'total_turns_in_session': total_turns,
            'total_tokens_in_session': total_tokens,
            'conversations': self.list_conversations()
        }


if __name__ == '__main__':
    # Ejemplo de uso
    memory = ConversationMemory(max_tokens=5000)
    
    # Añadir turnos
    memory.add_turn(
        user_question="¿Quién es Manuelita?",
        bot_response="Manuelita es una empresa agroindustrial diversificada...",
        rag_context="Empresa fundada en 1864...",
        sources=["manuelita_com_home.md"]
    )
    
    # Gestión de sesiones
    session = SessionManager()
    session.create_conversation("conv_1")
    current = session.get_current_conversation()
    if current:
        current.add_turn(
            user_question="¿Dónde están ubicadas?",
            bot_response="Tenemos sedes en varios países...",
            sources=["manuelita_com_contacto.md"]
        )
