"""
Herramienta Estructurada para Datos Concretos

Responde preguntas deterministas sobre contacto, horarios, ubicaciones, etc.
"""

import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StructuredDataTool:
    """Herramienta para consultas de datos estructurados."""
    
    def __init__(self, data_file: str = "tools/data/faq_structured.json"):
        """
        Inicializa la herramienta.
        
        Args:
            data_file: Ruta al archivo JSON con datos estructurados
        """
        self.data_file = data_file
        self.data: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Carga datos del archivo JSON."""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"✅ Datos estructurados cargados desde {self.data_file}")
            else:
                logger.warning(f"Archivo {self.data_file} no encontrado. Usando datos vacíos.")
                self.data = {'contact': {}, 'products': [], 'company_info': {}}
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            self.data = {'contact': {}, 'products': [], 'company_info': {}}
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Consulta la herramienta estructurada.
        
        Args:
            question: Pregunta del usuario
        
        Returns:
            Dict con respuesta, tipo de consulta, fuentes
        """
        question_lower = question.lower()
        
        # Detectar tipo de consulta
        if self._is_contact_question(question_lower):
            return self._handle_contact_query(question_lower)
        elif self._is_hours_question(question_lower):
            return self._handle_hours_query(question_lower)
        elif self._is_products_question(question_lower):
            return self._handle_products_query(question_lower)
        elif self._is_location_question(question_lower):
            return self._handle_location_query(question_lower)
        else:
            return {
                'success': False,
                'answer': None,
                'query_type': 'unknown',
                'confidence': 0.0
            }
    
    def _is_contact_question(self, text: str) -> bool:
        """Detecta si es pregunta sobre contacto."""
        keywords = ['teléfono', 'email', 'correo', 'contacto', 'comunicarse', 'llamar', 'escribir']
        return any(kw in text for kw in keywords)
    
    def _is_hours_question(self, text: str) -> bool:
        """Detecta si es pregunta sobre horarios."""
        keywords = ['horario', 'abierto', 'cierre', 'atienden', 'disponibilidad', 'cuando', 'qué hora']
        return any(kw in text for kw in keywords)
    
    def _is_products_question(self, text: str) -> bool:
        """Detecta si es pregunta sobre productos."""
        keywords = ['producto', 'venden', 'ofrecen', 'qué hacen', 'servicios', 'que producen']
        return any(kw in text for kw in keywords)
    
    def _is_location_question(self, text: str) -> bool:
        """Detecta si es pregunta sobre ubicación."""
        keywords = ['donde', 'ubicación', 'sede', 'domicilio', 'dirección', 'sucursal', 'local']
        return any(kw in text for kw in keywords)
    
    def _handle_contact_query(self, question: str) -> Dict[str, Any]:
        """Maneja consulta de contacto."""
        contact_info = self.data.get('contact', {})
        
        phone = contact_info.get('default_phone')
        email = contact_info.get('default_email')
        
        answer_parts = []
        if phone:
            answer_parts.append(f"Teléfono: {phone}")
        if email:
            answer_parts.append(f"Email: {email}")
        
        if not answer_parts:
            return {
                'success': False,
                'answer': "No tengo información de contacto disponible en la base de datos.",
                'query_type': 'contact',
                'confidence': 0.0
            }
        
        return {
            'success': True,
            'answer': "\n".join(answer_parts),
            'query_type': 'contact',
            'confidence': 0.95,
            'data': {'phone': phone, 'email': email}
        }
    
    def _handle_hours_query(self, question: str) -> Dict[str, Any]:
        """Maneja consulta de horarios."""
        hours = self.data.get('contact', {}).get('hours', {})
        
        if not hours:
            return {
                'success': False,
                'answer': "No tengo información de horarios disponible.",
                'query_type': 'hours',
                'confidence': 0.0
            }
        
        # Formatear horarios
        answer_parts = []
        for key, value in hours.items():
            answer_parts.append(f"• {key.replace('_', ' ').title()}: {value}")
        
        return {
            'success': True,
            'answer': "\n".join(answer_parts),
            'query_type': 'hours',
            'confidence': 0.90,
            'data': hours
        }
    
    def _handle_products_query(self, question: str) -> Dict[str, Any]:
        """Maneja consulta de productos."""
        products = self.data.get('products', [])
        
        if not products:
            return {
                'success': False,
                'answer': "No tengo información de productos.",
                'query_type': 'products',
                'confidence': 0.0
            }
        
        # Formatear productos
        product_names = [p.get('name', 'Producto') for p in products[:10]]
        answer = "Ofrecemos los siguientes productos:\n" + "\n".join(
            f"• {name}" for name in product_names
        )
        
        return {
            'success': True,
            'answer': answer,
            'query_type': 'products',
            'confidence': 0.85,
            'data': {'count': len(products), 'products': product_names}
        }
    
    def _handle_location_query(self, question: str) -> Dict[str, Any]:
        """Maneja consulta de ubicación."""
        locations = self.data.get('contact', {}).get('locations', [])
        
        if not locations:
            return {
                'success': False,
                'answer': "No tengo información de ubicaciones.",
                'query_type': 'location',
                'confidence': 0.0
            }
        
        # Formatear ubicaciones
        location_strs = []
        for loc in locations[:5]:
            name = loc.get('name', 'Sede')
            address = loc.get('address', 'Dirección no disponible')
            city = loc.get('city', '')
            location_strs.append(f"• {name}: {address}" + (f", {city}" if city else ""))
        
        answer = "Nuestras ubicaciones:\n" + "\n".join(location_strs)
        
        return {
            'success': True,
            'answer': answer,
            'query_type': 'location',
            'confidence': 0.88,
            'data': {'count': len(locations), 'locations': locations[:5]}
        }
    
    def get_available_queries(self) -> List[str]:
        """Retorna ejemplos de queries que puedo responder."""
        return [
            "¿Cuál es el número de teléfono?",
            "¿Cuál es el email de contacto?",
            "¿Cuál es el horario de atención?",
            "¿Qué productos venden?",
            "¿Dónde tienen sedes?",
            "¿Cuáles son sus ubicaciones?"
        ]


def is_structured_question(question: str) -> bool:
    """Determina si una pregunta debe ir a la herramienta estructurada."""
    keywords = [
        'teléfono', 'email', 'horario', 'abierto', 'donde', 'ubicación',
        'sede', 'dirección', 'producto', 'venden', 'contacto', 'llamar'
    ]
    return any(kw in question.lower() for kw in keywords)


if __name__ == '__main__':
    # Ejemplo de uso
    tool = StructuredDataTool()
    
    test_questions = [
        "¿Cuál es el teléfono de contacto?",
        "¿Qué horarios tienen?",
        "¿Dónde están ubicados?",
        "¿Qué productos venden?"
    ]
    
    for q in test_questions:
        result = tool.query(q)
        print(f"Q: {q}")
        print(f"A: {result['answer']}")
        print(f"Confianza: {result['confidence']}\n")
