"""
News Content Transformer

Specialized transformer for cleaning Manuelita news content while preserving publication dates.
"""

import re
from typing import Tuple, List, Set

from .base import BaseTransformer


class NewsTransformer(BaseTransformer):
    """Transformer specialized for news content with date preservation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preserved_dates: Set[str] = set()
    
    def _extract_dates(self, content: str) -> Set[str]:
        """Extract and preserve all date patterns before cleaning."""
        dates = set()
        
        # Pattern 1: Short date format "10 junio / 2025"
        short_dates = re.findall(
            r'(\d{1,2}\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*/\s*\d{4})', 
            content, re.IGNORECASE
        )
        for date_match in short_dates:
            dates.add(date_match[0])
        
        # Pattern 2: Full date format "**Palmira | 04 de diciembre de 2024.**"
        full_dates = re.findall(
            r'(\*\*[^|]+\|\s*\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}\.\*\*)', 
            content, re.IGNORECASE
        )
        for date_match in full_dates:
            dates.add(date_match[0])
        
        # Pattern 3: Simple date format "04 de diciembre de 2024"
        simple_dates = re.findall(
            r'(\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4})', 
            content, re.IGNORECASE
        )
        for date_match in simple_dates:
            dates.add(date_match[0])
        
        return dates
    
    def _is_date_line(self, line: str, preserved_dates: Set[str]) -> bool:
        """Check if a line contains preserved dates."""
        for date in preserved_dates:
            if date.strip() in line or any(part.strip() in line for part in date.split()):
                return True
        return False
    
    def _apply_specialized_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply news-specific content cleaning while preserving dates."""
        transformations = []
        
        # First, extract and preserve all dates
        self.preserved_dates = self._extract_dates(content)
        if self.preserved_dates:
            transformations.append('preserved_publication_dates')
        
        # Remove news-specific patterns
        news_patterns = {
            'related_articles': re.compile(
                r'(##\s+Articulos relacionados:.*)', 
                re.MULTILINE | re.DOTALL
            ),
            'article_previews': re.compile(
                r'(Leer más|Ver el informe aquí|Articulos relacionados:|Artículos relacionados:)', 
                re.MULTILINE
            ),
            'news_navigation': re.compile(
                r'(Noticias|Blog /.*$)', 
                re.MULTILINE
            )
        }
        
        # Apply news patterns
        for pattern_name, pattern in news_patterns.items():
            if pattern.search(content):
                content = pattern.sub('', content)
                transformations.append(f'removed_{pattern_name}')
        
        # Remove social media placeholders specific to news
        content = re.sub(r'^_{2,}$', '', content, flags=re.MULTILINE)
        if transformations:
            transformations.append('removed_social_media_placeholders')
        
        return content, transformations
    
    def _apply_line_by_line_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Override to add date preservation logic."""
        transformations = []
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines, but keep paragraph breaks
            if not line:
                if cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')
                continue
            
            # PRESERVE ALL DATE PATTERNS - check if line contains any preserved dates
            if self.config.patterns.preserve_dates and self._is_date_line(line, self.preserved_dates):
                cleaned_lines.append(line)
                continue
            
            # Skip lines that are only underscores or dashes
            if re.match(r'^[_\-]+$', line):
                continue
            
            # Skip WordPress related lines
            wordpress_lines = [
                '* Acerca de WordPress', '* WordPress.org', '* Documentación',
                '* Aprende WordPress', '* Soporte', '* Sugerencias', '* Buscar',
                'Acerca de WordPress', 'WordPress.org', 'Documentación',
                'Aprende WordPress', 'Soporte', 'Sugerencias', 'Buscar'
            ]
            if line in wordpress_lines:
                continue
            
            # Skip generic action words (including news-specific ones)
            generic_actions = [
                'Leer más', 'Conoce más', 'Conoce como lo hacemos',
                'Conoce cómo lo hacemos', 'Ver todas las noticias',
                'Facebook', 'Twitter', 'Línea de tiempo', 'Ver el informe aquí',
                'Articulos relacionados:', 'Artículos relacionados:'
            ]
            if line in generic_actions:
                continue
            
            # Skip social media underscores
            if line == '__' or re.match(r'^_{2,}$', line):
                continue
            
            # Skip very short lines that are only symbols
            if len(line) < 2 or re.match(r'^[^\w\s]+$', line):
                continue
            
            cleaned_lines.append(line)
        
        if len(cleaned_lines) < len(lines):
            transformations.append('applied_news_line_cleaning')
        
        # Final cleanup
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)  # Remove multiple consecutive empty lines
        result = result.strip()
        
        return result, transformations