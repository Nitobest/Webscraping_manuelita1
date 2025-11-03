"""
Script de debug para investigar el problema del chat
"""

import os
import logging
from config import config
from agent import ManuelitaAgent

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("=" * 80)
print("DEBUG: CONFIGURACIÓN ACTUAL")
print("=" * 80)
print(f"Modelo LLM: {config.llm.model}")
print(f"OpenAI API Key configurada: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"Google API Key configurada: {bool(os.getenv('GOOGLE_API_KEY'))}")
print(f"Temperature: {config.llm.temperature}")
print()

print("=" * 80)
print("DEBUG: INICIALIZANDO AGENTE")
print("=" * 80)
agent = ManuelitaAgent()
print()

print("=" * 80)
print("DEBUG: ESTADÍSTICAS DEL AGENTE")
print("=" * 80)
stats = agent.get_agent_stats()
print(f"RAG Available: {stats['rag_available']}")
print(f"Structured Tool Available: {stats['structured_tool_available']}")
print(f"LLM Available: {stats['llm_available']}")
print(f"LLM Object: {agent.llm}")
print(f"LLM Type: {type(agent.llm)}")
print()

if agent.llm:
    print("=" * 80)
    print("DEBUG: PROBANDO LLM DIRECTO")
    print("=" * 80)
    try:
        response = agent.llm.invoke("Di 'Hola, estoy funcionando'")
        print(f"Respuesta LLM: {response.content}")
    except Exception as e:
        print(f"❌ Error invocando LLM: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ LLM no está disponible!")
print()

print("=" * 80)
print("DEBUG: PROBANDO AGENT.PROCESS()")
print("=" * 80)
try:
    result = agent.process("¿Quién es Manuelita?", use_memory=False)
    print(f"Success: {result['success']}")
    print(f"Tool Used: {result['tool_used']}")
    print(f"Answer: {result['answer'][:100]}...")
except Exception as e:
    print(f"❌ Error procesando: {e}")
    import traceback
    traceback.print_exc()
