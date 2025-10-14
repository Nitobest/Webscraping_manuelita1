"""
Base Loader Classes

This module provides base classes for data loading (storage) operations.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ..logging_config import get_logger


@dataclass
class LoadResult:
    """Result of a data loading operation."""
    success: bool
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ContentItem:
    """Represents a piece of content to be loaded."""
    content: str
    metadata: Dict[str, Any]
    source_url: str
    content_type: str = "markdown"
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class BaseLoader(ABC):
    """Base class for content loaders."""
    
    def __init__(self, output_config: dict):
        self.output_config = output_config
        self.logger = get_logger()
        self.base_directory = Path(output_config.get('base_directory', 'data/processed'))
        self.include_metadata = output_config.get('include_metadata', True)
    
    def _create_output_directory(self, directory: Path) -> bool:
        """Create output directory if it doesn't exist."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory: {directory}", error=e)
            return False
    
    def _generate_filename(self, item: ContentItem, extension: str = ".md") -> str:
        """Generate a filename for the content item."""
        # Create a safe filename from URL
        from urllib.parse import urlparse
        parsed = urlparse(item.source_url)
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        path = parsed.path.strip('/').replace('/', '_').replace('-', '_')
        
        if not path:
            path = 'home'
        
        # Limit filename length
        if len(path) > 100:
            path = path[:100]
        
        return f"{domain}_{path}{extension}"
    
    def _create_metadata_file(self, items: List[ContentItem], output_dir: Path) -> Optional[Path]:
        """Create a metadata index file."""
        if not self.include_metadata:
            return None
        
        metadata_file = output_dir / "metadata.json"
        
        try:
            metadata_index = {
                'created_at': datetime.utcnow().isoformat(),
                'total_items': len(items),
                'items': []
            }
            
            for item in items:
                item_metadata = {
                    'source_url': item.source_url,
                    'content_type': item.content_type,
                    'timestamp': item.timestamp,
                    'filename': self._generate_filename(item),
                    'metadata': item.metadata
                }
                metadata_index['items'].append(item_metadata)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_index, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created metadata file", metadata_file=str(metadata_file))
            return metadata_file
            
        except Exception as e:
            self.logger.error("Failed to create metadata file", error=e)
            return None
    
    @abstractmethod
    def load_item(self, item: ContentItem, output_dir: Optional[Path] = None) -> LoadResult:
        """Load a single content item. To be implemented by subclasses."""
        pass
    
    @abstractmethod
    def load_batch(self, items: List[ContentItem], output_dir: Optional[Path] = None) -> List[LoadResult]:
        """Load multiple content items. To be implemented by subclasses."""
        pass
    
    def get_stats(self, results: List[LoadResult]) -> Dict[str, Any]:
        """Get statistics about loading operations."""
        successful = sum(1 for result in results if result.success)
        failed = len(results) - successful
        
        return {
            'total_items': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(results) if results else 0,
            'output_paths': [result.output_path for result in results if result.output_path]
        }