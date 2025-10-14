"""
File-based Content Loader

Handles saving content to organized file structures on disk.
"""

import json
from typing import List, Optional, Dict
from pathlib import Path

from .base import BaseLoader, ContentItem, LoadResult


class FileLoader(BaseLoader):
    """Loader that saves content to organized file structures."""
    
    def __init__(self, output_config: dict):
        super().__init__(output_config)
        self.file_format = output_config.get('file_format', 'markdown')
    
    def _get_file_extension(self) -> str:
        """Get file extension based on format."""
        extensions = {
            'markdown': '.md',
            'html': '.html',
            'json': '.json'
        }
        return extensions.get(self.file_format, '.md')
    
    def _format_content(self, item: ContentItem) -> str:
        """Format content based on the specified format."""
        if self.file_format == 'json':
            return json.dumps({
                'content': item.content,
                'metadata': item.metadata,
                'source_url': item.source_url,
                'timestamp': item.timestamp
            }, indent=2, ensure_ascii=False)
        
        elif self.file_format == 'html':
            # Convert markdown to basic HTML structure
            html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{item.metadata.get('title', 'Manuelita Content')}</title>
    <meta name="description" content="{item.metadata.get('description', '')}">
</head>
<body>
    <div class="content">
        <h1>Source: <a href="{item.source_url}">{item.source_url}</a></h1>
        <div class="metadata">
            <p><strong>Scraped at:</strong> {item.timestamp}</p>
            <p><strong>Title:</strong> {item.metadata.get('title', 'N/A')}</p>
        </div>
        <div class="main-content">
            {item.content.replace(chr(10), '<br>' + chr(10))}
        </div>
    </div>
</body>
</html>"""
            return html_content
        
        else:  # markdown (default)
            formatted_content = ""
            if self.include_metadata:
                formatted_content += f"# {item.source_url}\n\n"
                if item.metadata.get('title'):
                    formatted_content += f"**Title:** {item.metadata['title']}\n\n"
                if item.metadata.get('description'):
                    formatted_content += f"**Description:** {item.metadata['description']}\n\n"
                formatted_content += "---\n\n"
            
            formatted_content += item.content
            return formatted_content
    
    def load_item(self, item: ContentItem, output_dir: Optional[Path] = None) -> LoadResult:
        """Load a single content item to file."""
        try:
            # Determine output directory
            if output_dir is None:
                output_dir = self.base_directory
            
            # Create output directory
            if not self._create_output_directory(output_dir):
                return LoadResult(
                    success=False,
                    error_message=f"Failed to create output directory: {output_dir}"
                )
            
            # Generate filename
            extension = self._get_file_extension()
            filename = self._generate_filename(item, extension)
            output_path = output_dir / filename
            
            # Format and write content
            formatted_content = self._format_content(item)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            self.logger.info("Content saved to file",
                           source_url=item.source_url,
                           output_path=str(output_path),
                           format=self.file_format)
            
            self.logger.increment_counter('items_saved')
            
            return LoadResult(
                success=True,
                output_path=str(output_path),
                metadata={
                    'filename': filename,
                    'format': self.file_format,
                    'size_bytes': len(formatted_content.encode('utf-8'))
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to save content item",
                            error=e,
                            source_url=item.source_url)
            return LoadResult(
                success=False,
                error_message=str(e)
            )
    
    def load_batch(self, items: List[ContentItem], output_dir: Optional[Path] = None) -> List[LoadResult]:
        """Load multiple content items to files."""
        if output_dir is None:
            output_dir = self.base_directory
        
        self.logger.info(f"Starting batch file loading",
                        item_count=len(items),
                        output_dir=str(output_dir))
        
        results = []
        
        with self.logger.timed_operation("batch_file_loading", item_count=len(items)):
            # Create output directory
            if not self._create_output_directory(output_dir):
                # Return failure for all items if directory creation fails
                error_result = LoadResult(
                    success=False,
                    error_message=f"Failed to create output directory: {output_dir}"
                )
                return [error_result] * len(items)
            
            # Load each item
            for i, item in enumerate(items, 1):
                self.logger.debug(f"Loading item {i}/{len(items)}",
                                source_url=item.source_url)
                
                result = self.load_item(item, output_dir)
                results.append(result)
                
                if result.success:
                    self.logger.increment_counter('batch_items_success')
                else:
                    self.logger.increment_counter('batch_items_failed')
            
            # Create metadata index file
            self._create_metadata_file(items, output_dir)
        
        # Log summary
        stats = self.get_stats(results)
        self.logger.info("Batch loading completed",
                        **stats)
        
        return results
    
    def create_organized_structure(self, items: List[ContentItem], base_output_dir: Optional[Path] = None) -> Dict[str, List[LoadResult]]:
        """
        Create an organized directory structure based on content types.
        
        Returns:
            Dictionary mapping content types to their load results
        """
        if base_output_dir is None:
            base_output_dir = self.base_directory
        
        # Group items by content type or source domain
        organized_items = {}
        for item in items:
            # Determine organization key (could be content type, domain, etc.)
            from urllib.parse import urlparse
            domain = urlparse(item.source_url).netloc.replace('www.', '')
            
            # Create subdirectories based on content characteristics
            if '/noticias/' in item.source_url or '/manuelita-noticias/' in item.source_url:
                key = 'news'
            elif 'fundacionmanuelita' in domain:
                key = 'foundation'
            else:
                key = 'corporate'
            
            if key not in organized_items:
                organized_items[key] = []
            organized_items[key].append(item)
        
        # Load items into organized structure
        all_results = {}
        for content_type, type_items in organized_items.items():
            type_output_dir = base_output_dir / content_type
            results = self.load_batch(type_items, type_output_dir)
            all_results[content_type] = results
            
            self.logger.info(f"Organized loading completed for {content_type}",
                           content_type=content_type,
                           item_count=len(type_items),
                           output_dir=str(type_output_dir))
        
        return all_results