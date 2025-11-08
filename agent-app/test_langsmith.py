"""
Script de Prueba - Integración LangSmith

Verifica que la configuración de LangSmith esté correcta.
"""

import os
import sys
from pathlib import Path

# Asegurar que podemos importar los módulos locales
sys.path.insert(0, str(Path(__file__).parent))

def test_environment_variables():
    """Verifica variables de entorno."""
    print("\n" + "="*60)
    print("📋 VERIFICANDO VARIABLES DE ENTORNO")
    print("="*60)
    
    required_vars = {
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "false"),
        "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY", ""),
        "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT", "manuelita-agent"),
        "LANGCHAIN_ENDPOINT": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    }
    
    for var, value in required_vars.items():
        if var == "LANGCHAIN_API_KEY" and value:
            # Ocultar API key parcialmente
            display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            status = "✅"
        elif var == "LANGCHAIN_API_KEY" and not value:
            display_value = "(no configurada)"
            status = "⚠️ "
        else:
            display_value = value
            status = "✅" if value else "❌"
        
        print(f"{status} {var}: {display_value}")
    
    return bool(required_vars["LANGCHAIN_API_KEY"])


def test_langsmith_config():
    """Verifica módulo langsmith_config."""
    print("\n" + "="*60)
    print("🔧 VERIFICANDO MÓDULO LANGSMITH_CONFIG")
    print("="*60)
    
    try:
        from langsmith_config import langsmith_config, log_langsmith_info
        
        print("✅ Módulo importado correctamente")
        print("\nEstado de LangSmith:")
        log_langsmith_info()
        
        return True
    except ImportError as e:
        print(f"❌ Error importando módulo: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def test_config_integration():
    """Verifica integración con config.py."""
    print("\n" + "="*60)
    print("⚙️  VERIFICANDO INTEGRACIÓN CON CONFIG.PY")
    print("="*60)
    
    try:
        from config import config
        
        print(f"✅ Config importado correctamente")
        print(f"\nLangSmith en config:")
        print(f"  - Enabled: {config.langsmith.enabled}")
        print(f"  - Project: {config.langsmith.project_name}")
        print(f"  - API Key: {'✅ Configurada' if config.langsmith.api_key else '❌ No configurada'}")
        print(f"  - Endpoint: {config.langsmith.endpoint}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_langsmith_package():
    """Verifica que el paquete langsmith esté instalado."""
    print("\n" + "="*60)
    print("📦 VERIFICANDO PAQUETE LANGSMITH")
    print("="*60)
    
    try:
        import langsmith
        print(f"✅ Paquete langsmith instalado (versión: {langsmith.__version__})")
        return True
    except ImportError:
        print("❌ Paquete langsmith NO instalado")
        print("\nPara instalar:")
        print("  uv pip install langsmith")
        print("  # o")
        print("  pip install langsmith")
        return False


def test_agent_compatibility():
    """Verifica que el agente sea compatible con LangSmith."""
    print("\n" + "="*60)
    print("🤖 VERIFICANDO COMPATIBILIDAD CON AGENTE")
    print("="*60)
    
    try:
        # Importar sin inicializar (para no requerir API keys)
        import agent
        import rag
        
        print("✅ Módulos agent y rag importados correctamente")
        print("\nℹ️  LangSmith rastreará automáticamente:")
        print("  - Llamadas a LLM (OpenAI, Gemini, Ollama)")
        print("  - Búsquedas RAG (retrieval y reranking)")
        print("  - Operaciones de memoria")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_summary_report(results: dict):
    """Genera reporte final."""
    print("\n" + "="*60)
    print("📊 REPORTE FINAL")
    print("="*60)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nPruebas pasadas: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ¡TODO LISTO! LangSmith está correctamente configurado.")
        print("\n📋 Próximos pasos:")
        print("  1. Si aún no tienes API key:")
        print("     - Ve a https://smith.langchain.com")
        print("     - Crea una cuenta y obtén tu API key")
        print("     - Agrégala a tu archivo .env")
        print("\n  2. Para habilitar LangSmith:")
        print("     - En .env, cambia: LANGCHAIN_TRACING_V2=true")
        print("     - Reinicia la aplicación: streamlit run app.py")
        print("\n  3. Verifica trazas en:")
        print("     - https://smith.langchain.com")
    elif passed >= total - 1:
        print("\n⚠️  CASI LISTO. Falta instalar el paquete langsmith.")
        print("\n📋 Ejecuta:")
        print("  uv pip install langsmith")
        print("  # o")
        print("  pip install langsmith")
    else:
        print("\n❌ FALTAN ALGUNOS PASOS.")
        print("\n📋 Revisa los errores arriba y:")
        print("  1. Verifica que langsmith_config.py existe")
        print("  2. Verifica que config.py fue actualizado")
        print("  3. Instala langsmith: pip install langsmith")


def main():
    """Ejecuta todas las pruebas."""
    print("\n🔍 INICIANDO VERIFICACIÓN DE LANGSMITH")
    print("="*60)
    
    results = {
        "env_vars": test_environment_variables(),
        "langsmith_package": test_langsmith_package(),
        "langsmith_config": test_langsmith_config(),
        "config_integration": test_config_integration(),
        "agent_compatibility": test_agent_compatibility()
    }
    
    generate_summary_report(results)
    
    print("\n" + "="*60)
    print("Para más información, consulta: LANGSMITH_SETUP.md")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
