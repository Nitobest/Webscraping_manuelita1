#!/usr/bin/env python3
"""
Specialized News Cleaner script for Manuelita news content files.
Removes irrelevant content while ABSOLUTELY preserving publication dates and essential news information.
"""

import os
import re
import shutil
from pathlib import Path


class ManuelitaNewsCleaner:
    def __init__(self, input_dir="manuelita_news_content", output_dir="manuelita_news_content_cleaned"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Compile regex patterns for better performance
        self.patterns = {
            # Remove line numbers at the beginning (e.g., "1|", "123|")
            'line_numbers': re.compile(r'^\d+\|', re.MULTILINE),
            
            # Remove image references ![alt](url) or ![](url)
            'images': re.compile(r'!\[.*?\]\([^)]*\)', re.MULTILINE | re.DOTALL),
            
            # Convert markdown links [text](url) to just text, but keep meaningful text
            'markdown_links': re.compile(r'\[([^\]]+)\]\([^)]+\)', re.MULTILINE),
            
            # Remove standalone URLs (http/https)
            'standalone_urls': re.compile(r'https?://[^\s\)]+', re.MULTILINE),
            
            # Remove WordPress toolbar section and related content
            'wordpress_toolbar': re.compile(
                r'Ir a la barra de herramientas.*?(\* Buscar|$)', 
                re.MULTILINE | re.DOTALL
            ),
            
            # Remove WordPress menu items
            'wordpress_menu': re.compile(
                r'\* Acerca de WordPress.*?\* Buscar', 
                re.MULTILINE | re.DOTALL
            ),
            
            # Remove social sharing patterns
            'social_sharing': re.compile(
                r'(Compartir en (Facebook|Twitter|Linkedin)|Ir a Instagram)[^\n]*', 
                re.MULTILINE
            ),
            
            # Remove navigation elements and icons
            'navigation_icons': re.compile(
                r'(×|Cerrar|Volver a|Leer articulo|Leer artículo)', 
                re.MULTILINE
            ),
            
            # Remove specific WordPress/UI elements
            'ui_elements': re.compile(
                r'(Hitos (Mundiales|en Colombia)|Leer Historia)', 
                re.MULTILINE
            ),
            
            # Remove excessive whitespace and empty lines
            'excessive_whitespace': re.compile(r'\n\s*\n\s*\n', re.MULTILINE),
            
            # Remove standalone special characters and symbols
            'special_chars': re.compile(r'^[×\*\-_•▶]{1,3}$', re.MULTILINE),
            
            # Remove short meaningless lines (less than 3 characters, only symbols)
            'short_meaningless': re.compile(r'^[^\w\s]{1,2}$', re.MULTILINE),
            
            # Remove massive repeated content sections in related articles
            'massive_repeated_content': re.compile(
                r'(##\s+Articulos relacionados:.*)', 
                re.MULTILINE | re.DOTALL
            ),
        }

    def preserve_dates(self, content):
        """Extract and preserve all date patterns before cleaning."""
        preserved_dates = []
        
        # Pattern 1: Short date format "10 junio / 2025"
        short_dates = re.findall(r'(\d{1,2}\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*/\s*\d{4})', content, re.IGNORECASE)
        for date_match in short_dates:
            preserved_dates.append(date_match[0])
        
        # Pattern 2: Full date format "**Palmira | 04 de diciembre de 2024.**"
        full_dates = re.findall(r'(\*\*[^|]+\|\s*\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}\.\*\*)', content, re.IGNORECASE)
        for date_match in full_dates:
            preserved_dates.append(date_match[0])
            
        return preserved_dates

    def clean_content(self, content):
        """Clean the content using all defined patterns while preserving dates."""
        
        # First, preserve all dates
        preserved_dates = self.preserve_dates(content)
        
        # Remove line numbers first
        content = self.patterns['line_numbers'].sub('', content)
        
        # Remove WordPress toolbar section
        content = self.patterns['wordpress_toolbar'].sub('', content)
        
        # Remove WordPress menu items
        content = self.patterns['wordpress_menu'].sub('', content)
        
        # Remove images completely
        content = self.patterns['images'].sub('', content)
        
        # Remove massive repeated content sections (related articles)
        content = self.patterns['massive_repeated_content'].sub('', content)
        
        # Convert markdown links to text only (keep the text inside [])
        content = self.patterns['markdown_links'].sub(r'\1', content)
        
        # Remove standalone URLs
        content = self.patterns['standalone_urls'].sub('', content)
        
        # Remove social sharing elements
        content = self.patterns['social_sharing'].sub('', content)
        
        # Remove navigation icons and elements
        content = self.patterns['navigation_icons'].sub('', content)
        
        # Remove UI elements
        content = self.patterns['ui_elements'].sub('', content)
        
        # Remove special characters on their own lines
        content = self.patterns['special_chars'].sub('', content)
        
        # Remove short meaningless lines
        content = self.patterns['short_meaningless'].sub('', content)
        
        # Clean up excessive whitespace (replace multiple newlines with double newline)
        content = self.patterns['excessive_whitespace'].sub('\n\n', content)
        
        # Additional manual cleaning for specific patterns
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
            contains_date = False
            for date in preserved_dates:
                if date.strip() in line or any(part.strip() in line for part in date.split()):
                    contains_date = True
                    break
            
            # If line contains a date, keep it no matter what
            if contains_date:
                cleaned_lines.append(line)
                continue
            
            # Skip lines that are only underscores or dashes
            if re.match(r'^[_\-]+$', line):
                continue
                
            # Skip lines with only "Blog /" or similar navigation
            if re.match(r'^Blog\s*/.*$', line):
                continue
            
            # Skip WordPress related lines
            if line in ['* Acerca de WordPress', '* WordPress.org', '* Documentación', 
                       '* Aprende WordPress', '* Soporte', '* Sugerencias', '* Buscar',
                       'Acerca de WordPress', 'WordPress.org', 'Documentación',
                       'Aprende WordPress', 'Soporte', 'Sugerencias', 'Buscar']:
                continue
                
            # Skip generic action words that don't add value
            if line in ['Leer más', 'Conoce más', 'Conoce como lo hacemos', 
                       'Conoce cómo lo hacemos', 'Conoce nuestras ofertas laborales',
                       'Ver todas las noticias', 'Ver nuestro informe de sostenibilidad 2023 - 2024',
                       'Manuelita Sustainability Report 2023-2024 english version',
                       'Facebook', 'Twitter', 'Línea de tiempo', 'Ver el informe aquí',
                       'Articulos relacionados:', 'Artículos relacionados:']:
                continue
                
            # Skip lines that are just underscores (social media placeholders)
            if line == '__' or re.match(r'^_{2,}$', line):
                continue
                
            # Skip lines that are only numbers (like years) if they're standalone and NOT dates
            if re.match(r'^\d{4}$', line) and len(line) == 4:
                # Keep if it's a reasonable year, skip if it seems like a line number
                if 1800 <= int(line) <= 2030:
                    cleaned_lines.append(line)
                continue
                
            # Skip lines that are only symbols or very short
            if len(line) < 2 or re.match(r'^[^\w\s]+$', line):
                continue
                
            cleaned_lines.append(line)
        
        # Join lines and do final cleanup
        result = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive empty lines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Trim leading/trailing whitespace
        result = result.strip()
        
        # Final check: ensure all preserved dates are still present
        for date in preserved_dates:
            if date.strip() not in result:
                # Re-add the date at the beginning if it was accidentally removed
                result = date.strip() + '\n\n' + result
        
        return result

    def process_file(self, input_path, output_path):
        """Process a single file."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean the content
            cleaned_content = self.clean_content(content)
            
            # Write cleaned content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            return True
            
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False

    def process_all_files(self):
        """Process all markdown files in the input directory."""
        if not self.input_dir.exists():
            print(f"Error: Input directory '{self.input_dir}' does not exist.")
            return False
        
        # Create output directory
        if self.output_dir.exists():
            print(f"Output directory '{self.output_dir}' already exists. Removing...")
            shutil.rmtree(self.output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all markdown files
        md_files = list(self.input_dir.glob('*.md'))
        
        if not md_files:
            print(f"No markdown files found in '{self.input_dir}'")
            return False
        
        print(f"Found {len(md_files)} files to process...")
        
        processed = 0
        failed = 0
        
        for md_file in md_files:
            output_path = self.output_dir / md_file.name
            print(f"Processing: {md_file.name}")
            
            if self.process_file(md_file, output_path):
                processed += 1
            else:
                failed += 1
        
        print(f"\nProcessing complete!")
        print(f"Successfully processed: {processed} files")
        print(f"Failed: {failed} files")
        print(f"Output directory: {self.output_dir}")
        
        return True


def main():
    """Main function to run the news cleaner."""
    import sys
    
    print("Manuelita NEWS Content Cleaner - SPECIALIZED for News with Date Preservation")
    print("=" * 80)
    
    # Allow command line arguments to specify directories
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        print(f"Using custom directories: '{input_dir}' -> '{output_dir}'")
        cleaner = ManuelitaNewsCleaner(input_dir, output_dir)
    else:
        # Default directories
        cleaner = ManuelitaNewsCleaner()
    
    # Process all files
    success = cleaner.process_all_files()
    
    if success:
        print("\n✅ All news files have been successfully cleaned with DATES PRESERVED!")
    else:
        print("\n❌ Some errors occurred during processing.")


if __name__ == "__main__":
    main()