"""
Agente Inteligente con Enrutamiento

Decide dinámicamente entre RAG y Structured Tool.
"""

import os
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from rag import RAGSystem
from tools.structured_tool import StructuredDataTool, is_structured_question
from memory import ConversationMemory

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
except ImportError:
    logger.warning("LangChain Google GenAI no instalado. Usando stub.")
    ChatGoogleGenerativeAI = None


class ManuelitaAgent:
    """Agente inteligente con enrutamiento RAG/Structured."""
    
    def __init__(self, api_key: Optional[str] = None, use_ollama: bool = False):
        """
        Inicializa el agente.
        
        Args:
            api_key: API key para OpenAI (si None, intenta leer de env)
            use_ollama: Si True, usa Ollama en lugar de OpenAI
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_ollama = use_ollama
        self.rag = None
        self.structured_tool = None
        self.llm = None
        self.memory = ConversationMemory(max_tokens=20000)
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Inicializa componentes."""
        try:
            logger.info("Inicializando Agente Manuelita...")
            
            # RAG
            self.rag = RAGSystem(
                data_dir="../data/raw/processed",
                vectordb_dir="./vectordb"
            )
            
            # Structured Tool
            self.structured_tool = StructuredDataTool(
                data_file="tools/data/faq_structured.json"
            )
            
            # LLM
            self._initialize_llm()
            
            logger.info("✅ Agente inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando agente: {e}")
    
    def _initialize_llm(self) -> None:
        """Inicializa el modelo LLM."""
        try:
            if self.use_ollama:
                logger.info("Usando Ollama para LLM...")
                # Para Ollama, usaríamos: ollama pull qwen:4b
                # Y luego integrar con LangChain
                logger.warning("Ollama integration pendiente. Usando stub.")
                self.llm = None
            else:
                if not self.api_key:
                    logger.warning("API Key no configurada. Usando respuestas predeterminadas.")
                    self.llm = None
                    return
                
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-pro",
                    temperature=0.05,
                    google_api_key=self.api_key
                )
                logger.info("✅ LLM Gemini inicializado")
        except Exception as e:
            logger.error(f"Error inicializando LLM: {e}")
            self.llm = None
    
    def route_question(self, question: str) -> str:
        """Determina qué herramienta usar."""
        if is_structured_question(question):
            return "structured"
        return "rag"
    
    def process(self, question: str, use_memory: bool = True,
                temperature: float = 0.05, top_k: int = 4,
                max_tokens: int = 500) -> Dict[str, Any]:
        """
        Procesa una pregunta del usuario.
        
        Args:
            question: Pregunta del usuario
            use_memory: Si incluir contexto de conversación
            temperature: Temperatura del LLM
            top_k: Número de documentos RAG a recuperar
            max_tokens: Máximo de tokens en respuesta
        
        Returns:
            Dict con respuesta, tool usado, contexto, etc.
        """
        try:
            # 1. Determinar herramienta
            tool_choice = self.route_question(question)
            
            # 2. Recuperar contexto
            if tool_choice == "structured":
                result = self.structured_tool.query(question)
                response = result.get('answer', 'No pude responder.')
                sources = [result.get('query_type', 'structured')]
                context_used = ""
            else:
                rag_result = self.rag.search(question, top_k=top_k)
                context_used = rag_result['context']
                sources = [doc['source'] for doc in rag_result['documents']]
                
                # Generar respuesta con LLM si disponible
                if self.llm:
                    response = self._generate_response(
                        question, context_used, temperature, max_tokens
                    )
                else:
                    response = f"Basado en el contexto disponible:\n\n{context_used[:500]}..."
            
            # 3. Guardar en memoria
            if use_memory:
                self.memory.add_turn(
                    user_question=question,
                    bot_response=response,
                    rag_context=context_used if tool_choice == "rag" else None,
                    sources=sources,
                    tool_used=tool_choice
                )
            
            # 4. Retornar resultado
            return {
                'question': question,
                'answer': response,
                'tool_used': tool_choice,
                'sources': sources,
                'context_used': context_used[:300] if context_used else "",
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error procesando pregunta: {e}")
            return {
                'question': question,
                'answer': f"Error: {str(e)}",
                'tool_used': 'error',
                'sources': [],
                'success': False
            }
    
    def _generate_response(self, question: str, context: str,
                          temperature: float, max_tokens: int) -> str:
        """Genera respuesta con el LLM."""
        try:
            if not self.llm:
                return "LLM no disponible."
            
            prompt = f"""Eres un asistente oficial de Manuelita.
Responde SOLO basado en el contexto proporcionado.
Si no encuentras información en el contexto, di que no tienes suficiente información.

CONTEXTO:
{context}

PREGUNTA: {question}

RESPUESTA:"""
            
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return "No pude generar una respuesta."
    
    def get_memory_context(self) -> str:
        """Retorna el contexto de memoria para el prompt."""
        return self.memory.get_conversation_context()
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del agente."""
        return {
            'rag_available': self.rag is not None,
            'structured_tool_available': self.structured_tool is not None,
            'llm_available': self.llm is not None,
            'memory_stats': self.memory.get_stats(),
            'rag_stats': self.rag.get_stats() if self.rag else {},
            'use_ollama': self.use_ollama
        }


if __name__ == '__main__':
    # Ejemplo
    agent = ManuelitaAgent()
    
    result = agent.process("¿Quién es Manuelita?")
    print(f"Q: {result['question']}")
    print(f"A: {result['answer']}")
    print(f"Tool: {result['tool_used']}")
