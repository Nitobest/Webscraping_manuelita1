"""
Corporate Content Transformer

Specialized transformer for cleaning Manuelita corporate content.
"""

import re
from typing import Tuple, List

from .base import BaseTransformer


class CorporateTransformer(BaseTransformer):
    """Transformer specialized for corporate content cleaning."""
    
    def _apply_specialized_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply corporate-specific content cleaning."""
        transformations = []
        
        # Remove corporate-specific UI elements
        corporate_patterns = {
            'corporate_navigation': re.compile(
                r'(Perfil Corporativo|Gobierno Corporativo|Estrategia Corporativa|Plataformas de Negocios)', 
                re.MULTILINE
            ),
            'product_navigation': re.compile(
                r'(Alimenticio|Energético|Otros|Ver productos)', 
                re.MULTILINE
            ),
            'sustainability_navigation': re.compile(
                r'(Ambiental|Social|Económico|Ver informe de sostenibilidad)', 
                re.MULTILINE
            )
        }
        
        # Apply corporate patterns
        for pattern_name, pattern in corporate_patterns.items():
            if pattern.search(content):
                content = pattern.sub('', content)
                transformations.append(f'removed_{pattern_name}')
        
        # Remove specific corporate boilerplate text
        boilerplate_patterns = [
            r'Manuelita Sustainability Report \d{4}-\d{4} english version',
            r'Ver nuestro informe de sostenibilidad \d{4} - \d{4}',
            r'Conoce nuestras ofertas laborales',
            r'Conoce como lo hacemos',
            r'Cultivando progreso y bienestar'
        ]
        
        for pattern in boilerplate_patterns:
            regex = re.compile(pattern, re.MULTILINE)
            if regex.search(content):
                content = regex.sub('', content)
                transformations.append('removed_corporate_boilerplate')
        
        # Clean up corporate section separators
        content = re.sub(r'^[\*\-_]{3,}$', '', content, flags=re.MULTILINE)
        if transformations:
            transformations.append('cleaned_section_separators')
        
        return content, transformations