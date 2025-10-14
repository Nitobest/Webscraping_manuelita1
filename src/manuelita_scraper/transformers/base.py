"""
Base Transformer Classes

This module provides base classes for data transformation (content cleaning) operations.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..config import CleaningConfig
from ..logging_config import get_logger


@dataclass
class TransformationResult:
    """Result of a content transformation operation."""
    original_content: str
    cleaned_content: str
    transformations_applied: List[str]
    success: bool = True
    error_message: Optional[str] = None


class BaseTransformer(ABC):
    """Base class for content transformers."""
    
    def __init__(self, config: CleaningConfig):
        self.config = config
        self.logger = get_logger()
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for better performance."""
        patterns = {
            # Basic cleaning patterns
            'line_numbers': re.compile(r'^\d+\|', re.MULTILINE),
            'images': re.compile(r'!\[.*?\]\([^)]*\)', re.MULTILINE | re.DOTALL),
            'markdown_links': re.compile(r'\[([^\]]+)\]\([^)]+\)', re.MULTILINE),
            'standalone_urls': re.compile(r'https?://[^\s\)]+', re.MULTILINE),
            'excessive_whitespace': re.compile(r'\n\s*\n\s*\n', re.MULTILINE),
            'special_chars': re.compile(r'^[×\*\-_•▶]{1,3}$', re.MULTILINE),
            'short_meaningless': re.compile(r'^[^\w\s]{1,2}$', re.MULTILINE),
        }
        
        # Add WordPress-specific patterns if enabled
        if self.config.patterns.remove_navigation:
            patterns.update({
                'wordpress_toolbar': re.compile(
                    r'Ir a la barra de herramientas.*?Buscar', 
                    re.MULTILINE | re.DOTALL
                ),
                'wordpress_menu': re.compile(
                    r'\* Acerca de WordPress.*?\* Buscar', 
                    re.MULTILINE | re.DOTALL
                ),
            })
        
        # Add social media patterns if enabled
        if self.config.patterns.remove_social_media:
            patterns['social_sharing'] = re.compile(
                r'(Compartir en (Facebook|Twitter|Linkedin)|Ir a Instagram)[^\n]*', 
                re.MULTILINE
            )
            patterns['navigation_icons'] = re.compile(
                r'(×|Cerrar|Volver a|Leer articulo|Leer artículo)', 
                re.MULTILINE
            )
        
        # Add custom patterns from configuration
        for custom_pattern in self.config.patterns.custom_patterns:
            patterns[custom_pattern.name] = re.compile(
                custom_pattern.pattern, 
                re.MULTILINE | re.DOTALL
            )
        
        return patterns
    
    def _apply_basic_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply basic content cleaning transformations."""
        transformations = []
        
        # Remove line numbers
        if 'line_numbers' in self.patterns:
            content = self.patterns['line_numbers'].sub('', content)
            transformations.append('removed_line_numbers')
        
        # Remove images
        if 'images' in self.patterns:
            content = self.patterns['images'].sub('', content)
            transformations.append('removed_images')
        
        # Convert markdown links to text
        if 'markdown_links' in self.patterns:
            content = self.patterns['markdown_links'].sub(r'\1', content)
            transformations.append('converted_links_to_text')
        
        # Remove standalone URLs
        if 'standalone_urls' in self.patterns:
            content = self.patterns['standalone_urls'].sub('', content)
            transformations.append('removed_standalone_urls')
        
        return content, transformations
    
    def _apply_navigation_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply navigation and UI element cleaning."""
        transformations = []
        
        if not self.config.patterns.remove_navigation:
            return content, transformations
        
        # Remove WordPress elements
        if 'wordpress_toolbar' in self.patterns:
            content = self.patterns['wordpress_toolbar'].sub('', content)
            transformations.append('removed_wordpress_toolbar')
        
        if 'wordpress_menu' in self.patterns:
            content = self.patterns['wordpress_menu'].sub('', content)
            transformations.append('removed_wordpress_menu')
        
        return content, transformations
    
    def _apply_social_media_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply social media element cleaning."""
        transformations = []
        
        if not self.config.patterns.remove_social_media:
            return content, transformations
        
        if 'social_sharing' in self.patterns:
            content = self.patterns['social_sharing'].sub('', content)
            transformations.append('removed_social_sharing')
        
        if 'navigation_icons' in self.patterns:
            content = self.patterns['navigation_icons'].sub('', content)
            transformations.append('removed_navigation_icons')
        
        return content, transformations
    
    def _apply_custom_patterns(self, content: str) -> Tuple[str, List[str]]:
        """Apply custom cleaning patterns from configuration."""
        transformations = []
        
        for custom_pattern in self.config.patterns.custom_patterns:
            if custom_pattern.name in self.patterns:
                content = self.patterns[custom_pattern.name].sub(
                    custom_pattern.replacement, content
                )
                transformations.append(f'applied_custom_{custom_pattern.name}')
        
        return content, transformations
    
    def _apply_whitespace_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply whitespace and formatting cleanup."""
        transformations = []
        
        # Remove special characters on their own lines
        if 'special_chars' in self.patterns:
            content = self.patterns['special_chars'].sub('', content)
            transformations.append('removed_special_chars')
        
        # Remove short meaningless lines
        if 'short_meaningless' in self.patterns:
            content = self.patterns['short_meaningless'].sub('', content)
            transformations.append('removed_short_meaningless')
        
        # Clean up excessive whitespace
        if 'excessive_whitespace' in self.patterns:
            content = self.patterns['excessive_whitespace'].sub('\n\n', content)
            transformations.append('cleaned_excessive_whitespace')
        
        return content, transformations
    
    def _apply_line_by_line_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply line-by-line content cleaning."""
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
            
            # Skip generic action words
            generic_actions = [
                'Leer más', 'Conoce más', 'Conoce como lo hacemos',
                'Conoce cómo lo hacemos', 'Ver todas las noticias',
                'Facebook', 'Twitter', 'Línea de tiempo'
            ]
            if line in generic_actions:
                continue
            
            # Skip very short lines that are only symbols
            if len(line) < 2 or re.match(r'^[^\w\s]+$', line):
                continue
            
            cleaned_lines.append(line)
        
        if len(cleaned_lines) < len(lines):
            transformations.append('applied_line_by_line_cleaning')
        
        # Final cleanup
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)  # Remove multiple consecutive empty lines
        result = result.strip()
        
        return result, transformations
    
    @abstractmethod
    def _apply_specialized_cleaning(self, content: str) -> Tuple[str, List[str]]:
        """Apply specialized cleaning specific to content type. To be implemented by subclasses."""
        pass
    
    def transform_content(self, content: str) -> TransformationResult:
        """Transform (clean) the given content."""
        try:
            original_content = content
            all_transformations = []
            
            with self.logger.timed_operation("content_transformation"):
                # Apply transformations in order
                content, trans = self._apply_basic_cleaning(content)
                all_transformations.extend(trans)
                
                content, trans = self._apply_navigation_cleaning(content)
                all_transformations.extend(trans)
                
                content, trans = self._apply_social_media_cleaning(content)
                all_transformations.extend(trans)
                
                content, trans = self._apply_custom_patterns(content)
                all_transformations.extend(trans)
                
                content, trans = self._apply_specialized_cleaning(content)
                all_transformations.extend(trans)
                
                content, trans = self._apply_whitespace_cleaning(content)
                all_transformations.extend(trans)
                
                content, trans = self._apply_line_by_line_cleaning(content)
                all_transformations.extend(trans)
            
            self.logger.increment_counter('content_transformations')
            
            return TransformationResult(
                original_content=original_content,
                cleaned_content=content,
                transformations_applied=all_transformations,
                success=True
            )
            
        except Exception as e:
            self.logger.error("Content transformation failed", error=e)
            return TransformationResult(
                original_content=content,
                cleaned_content=content,  # Return original on failure
                transformations_applied=[],
                success=False,
                error_message=str(e)
            )
    
    def transform_file(self, input_path: str, output_path: str) -> bool:
        """Transform content from input file and save to output file."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = self.transform_content(content)
            
            if result.success:
                # Create output directory if it doesn't exist
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.cleaned_content)
                
                self.logger.info("File transformation completed",
                               input_path=input_path,
                               output_path=output_path,
                               transformations=len(result.transformations_applied))
                return True
            else:
                self.logger.error("File transformation failed",
                                input_path=input_path,
                                error=result.error_message)
                return False
                
        except Exception as e:
            self.logger.error("File processing failed", error=e,
                            input_path=input_path, output_path=output_path)
            return False
    
    def transform_directory(self, input_dir: str, output_dir: str, 
                          file_pattern: str = "*.md") -> Dict[str, bool]:
        """Transform all files in a directory."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return {}
        
        results = {}
        files = list(input_path.glob(file_pattern))
        
        self.logger.info(f"Starting directory transformation",
                        input_dir=input_dir,
                        output_dir=output_dir,
                        file_count=len(files))
        
        for file_path in files:
            relative_path = file_path.relative_to(input_path)
            output_file = output_path / relative_path
            
            success = self.transform_file(str(file_path), str(output_file))
            results[str(relative_path)] = success
            
            if success:
                self.logger.increment_counter('files_transformed')
            else:
                self.logger.increment_counter('files_failed')
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Directory transformation completed",
                        total_files=len(files),
                        successful=successful,
                        failed=len(files) - successful)
        
        return results