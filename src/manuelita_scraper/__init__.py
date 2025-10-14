"""
Manuelita Scraper - AI-powered web scraping pipeline

This package provides a complete ETL pipeline for scraping and processing
Manuelita corporate and news content.
"""

from .pipeline import ManuelitaPipeline
from .config import AppConfig, init_config, get_config
from .logging_config import get_logger, init_logging

# Extractors
from .extractors.corporate import CorporateExtractor
from .extractors.news import NewsExtractor

# Transformers  
from .transformers.corporate import CorporateTransformer
from .transformers.news import NewsTransformer

# Loaders
from .loaders.file_loader import FileLoader, ContentItem

__version__ = "0.2.0"
__author__ = "AI Engineering Team"
__description__ = "AI-powered web scraping pipeline for Manuelita corporate content extraction"

__all__ = [
    # Main pipeline
    "ManuelitaPipeline",
    
    # Configuration
    "AppConfig", 
    "init_config",
    "get_config",
    
    # Logging
    "get_logger",
    "init_logging",
    
    # Extractors
    "CorporateExtractor",
    "NewsExtractor", 
    
    # Transformers
    "CorporateTransformer",
    "NewsTransformer",
    
    # Loaders
    "FileLoader",
    "ContentItem",
]