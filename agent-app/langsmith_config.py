"""
Configuración de LangSmith para Observabilidad

Proporciona trazabilidad y monitoreo de interacciones del agente.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """Gestiona la configuración y estado de LangSmith."""
    
    def __init__(self):
        self.enabled = self._check_enabled()
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "manuelita-agent")
        self.api_key = os.getenv("LANGCHAIN_API_KEY", "")
        self.endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
        
        if self.enabled:
            self._setup_environment()
    
    def _check_enabled(self) -> bool:
        """Verifica si LangSmith está habilitado."""
        tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower()
        return tracing in ["true", "1", "yes"]
    
    def _setup_environment(self) -> None:
        """Configura las variables de entorno necesarias para LangSmith."""
        if not self.api_key:
            logger.warning(
                "⚠️ LANGCHAIN_TRACING_V2=true pero LANGCHAIN_API_KEY no está configurada. "
                "LangSmith no funcionará correctamente."
            )
            return
        
        # Configurar variables de entorno
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = self.project_name
        os.environ["LANGCHAIN_ENDPOINT"] = self.endpoint
        os.environ["LANGCHAIN_API_KEY"] = self.api_key
        
        logger.info(f"✅ LangSmith habilitado - Proyecto: {self.project_name}")
    
    def enable(self, api_key: Optional[str] = None, project_name: Optional[str] = None) -> bool:
        """
        Habilita LangSmith dinámicamente.
        
        Args:
            api_key: API key de LangSmith (opcional si ya está en env)
            project_name: Nombre del proyecto (opcional)
        
        Returns:
            True si se habilitó exitosamente
        """
        if api_key:
            self.api_key = api_key
            os.environ["LANGCHAIN_API_KEY"] = api_key
        
        if project_name:
            self.project_name = project_name
            os.environ["LANGCHAIN_PROJECT"] = project_name
        
        if not self.api_key:
            logger.error("❌ No se puede habilitar LangSmith: falta API key")
            return False
        
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        self.enabled = True
        
        logger.info(f"✅ LangSmith habilitado - Proyecto: {self.project_name}")
        return True
    
    def disable(self) -> None:
        """Deshabilita LangSmith temporalmente."""
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        self.enabled = False
        logger.info("🔴 LangSmith deshabilitado")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual de LangSmith."""
        return {
            "enabled": self.enabled,
            "project": self.project_name,
            "api_key_configured": bool(self.api_key),
            "endpoint": self.endpoint
        }
    
    @contextmanager
    def trace_session(self, session_name: str):
        """
        Context manager para rastrear una sesión específica.
        
        Usage:
            with langsmith_config.trace_session("chat-session-123"):
                result = agent.process(question)
        """
        if not self.enabled:
            yield
            return
        
        try:
            # Cambiar temporalmente el proyecto
            original_project = os.getenv("LANGCHAIN_PROJECT")
            os.environ["LANGCHAIN_PROJECT"] = f"{self.project_name}-{session_name}"
            
            logger.debug(f"📊 Iniciando traza: {session_name}")
            yield
            
        finally:
            # Restaurar proyecto original
            if original_project:
                os.environ["LANGCHAIN_PROJECT"] = original_project
            logger.debug(f"✅ Traza completada: {session_name}")


# Instancia global
langsmith_config = LangSmithConfig()


def get_langsmith_url(run_id: str) -> str:
    """
    Genera URL de LangSmith para una ejecución específica.
    
    Args:
        run_id: ID de la ejecución
    
    Returns:
        URL completa de LangSmith
    """
    if not langsmith_config.enabled:
        return ""
    
    return f"https://smith.langchain.com/o/default/p/{langsmith_config.project_name}/r/{run_id}"


def log_langsmith_info() -> None:
    """Imprime información sobre el estado de LangSmith."""
    status = langsmith_config.get_status()
    
    if status['enabled']:
        print("=" * 60)
        print("🔍 LANGSMITH OBSERVABILITY HABILITADA")
        print("=" * 60)
        print(f"📊 Proyecto: {status['project']}")
        print(f"🔑 API Key: {'✅ Configurada' if status['api_key_configured'] else '❌ No configurada'}")
        print(f"🌐 Endpoint: {status['endpoint']}")
        print(f"📍 Ver trazas en: https://smith.langchain.com")
        print("=" * 60)
    else:
        print("=" * 60)
        print("ℹ️  LangSmith deshabilitado")
        print("=" * 60)
        print("Para habilitarlo, configura en .env:")
        print("  LANGCHAIN_TRACING_V2=true")
        print("  LANGCHAIN_API_KEY=tu-api-key")
        print("=" * 60)


if __name__ == '__main__':
    # Test de configuración
    log_langsmith_info()
    
    print("\nEstado actual:")
    import json
    print(json.dumps(langsmith_config.get_status(), indent=2))
