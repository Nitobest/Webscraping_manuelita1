"""
Main ETL Pipeline Orchestrator

This module provides the main pipeline class that coordinates
Extract → Transform → Load operations.
"""

from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from .config import AppConfig, init_config
from .logging_config import setup_logging_from_config, get_logger
from .extractors.corporate import CorporateExtractor
from .extractors.news import NewsExtractor
from .transformers.corporate import CorporateTransformer
from .transformers.news import NewsTransformer
from .loaders.file_loader import FileLoader, ContentItem


class ManuelitaPipeline:
    """Main pipeline orchestrator for Manuelita content scraping and processing."""
    
    def __init__(self, environment: str = "development"):
        self.config = init_config(environment)
        self.logger = setup_logging_from_config(environment)
        
        # Initialize components
        self._corporate_extractor: Optional[CorporateExtractor] = None
        self._news_extractor: Optional[NewsExtractor] = None
        self._corporate_transformer: Optional[CorporateTransformer] = None
        self._news_transformer: Optional[NewsTransformer] = None
        self._loader: Optional[FileLoader] = None
    
    @property
    def corporate_extractor(self) -> CorporateExtractor:
        """Lazy initialization of corporate extractor."""
        if self._corporate_extractor is None:
            self._corporate_extractor = CorporateExtractor(self.config.scraping)
        return self._corporate_extractor
    
    @property
    def news_extractor(self) -> NewsExtractor:
        """Lazy initialization of news extractor."""
        if self._news_extractor is None:
            self._news_extractor = NewsExtractor(self.config.scraping)
        return self._news_extractor
    
    @property
    def corporate_transformer(self) -> CorporateTransformer:
        """Lazy initialization of corporate transformer."""
        if self._corporate_transformer is None:
            self._corporate_transformer = CorporateTransformer(self.config.cleaning)
        return self._corporate_transformer
    
    @property
    def news_transformer(self) -> NewsTransformer:
        """Lazy initialization of news transformer."""
        if self._news_transformer is None:
            self._news_transformer = NewsTransformer(self.config.cleaning)
        return self._news_transformer
    
    @property
    def loader(self) -> FileLoader:
        """Lazy initialization of loader."""
        if self._loader is None:
            output_config = {
                'base_directory': self.config.scraping.output.base_directory,
                'file_format': self.config.scraping.output.file_format,
                'include_metadata': self.config.scraping.output.include_metadata
            }
            self._loader = FileLoader(output_config)
        return self._loader
    
    def extract_corporate_content(self) -> List[Dict[str, Any]]:
        """Extract corporate content from configured URLs."""
        self.logger.info("Starting corporate content extraction")
        
        urls = self.config.scraping.targets.corporate_urls
        if not urls:
            self.logger.warning("No corporate URLs configured")
            return []
        
        with self.logger.timed_operation("corporate_extraction", url_count=len(urls)):
            results = self.corporate_extractor.extract_multiple_urls(urls)
        
        # Convert to dict format for pipeline processing
        extracted_data = []
        for result in results:
            if result.success:
                extracted_data.append({
                    'url': result.url,
                    'content': result.content,
                    'metadata': result.metadata,
                    'discovered_links': result.discovered_links
                })
        
        self.logger.info("Corporate extraction completed", 
                        total_extracted=len(extracted_data))
        return extracted_data
    
    def extract_news_content(self) -> tuple[List[Dict[str, Any]], Set[str]]:
        """Extract news content with link discovery."""
        self.logger.info("Starting news content extraction")
        
        urls = self.config.scraping.targets.news_base_urls
        if not urls:
            self.logger.warning("No news URLs configured")
            return [], set()
        
        with self.logger.timed_operation("news_extraction", url_count=len(urls)):
            results = self.news_extractor.extract_multiple_urls(urls)
        
        # Convert to dict format and collect discovered links
        extracted_data = []
        all_discovered_links = set()
        
        for result in results:
            if result.success:
                extracted_data.append({
                    'url': result.url,
                    'content': result.content,
                    'metadata': result.metadata,
                    'discovered_links': result.discovered_links
                })
                all_discovered_links.update(result.discovered_links)
        
        # Save discovered links
        if all_discovered_links:
            self.news_extractor.save_discovered_links(all_discovered_links, "discovered_news_links.json")
        
        self.logger.info("News extraction completed", 
                        total_extracted=len(extracted_data),
                        discovered_links=len(all_discovered_links))
        
        return extracted_data, all_discovered_links
    
    def transform_corporate_content(self, extracted_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform (clean) corporate content."""
        self.logger.info("Starting corporate content transformation")
        
        transformed_data = []
        
        with self.logger.timed_operation("corporate_transformation", item_count=len(extracted_data)):
            for item in extracted_data:
                result = self.corporate_transformer.transform_content(item['content'])
                
                if result.success:
                    transformed_data.append({
                        'url': item['url'],
                        'content': result.cleaned_content,
                        'metadata': item['metadata'],
                        'transformations_applied': result.transformations_applied
                    })
                else:
                    self.logger.warning("Content transformation failed",
                                      url=item['url'],
                                      error=result.error_message)
        
        self.logger.info("Corporate transformation completed",
                        total_transformed=len(transformed_data))
        return transformed_data
    
    def transform_news_content(self, extracted_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform (clean) news content."""
        self.logger.info("Starting news content transformation")
        
        transformed_data = []
        
        with self.logger.timed_operation("news_transformation", item_count=len(extracted_data)):
            for item in extracted_data:
                result = self.news_transformer.transform_content(item['content'])
                
                if result.success:
                    transformed_data.append({
                        'url': item['url'],
                        'content': result.cleaned_content,
                        'metadata': item['metadata'],
                        'transformations_applied': result.transformations_applied
                    })
                else:
                    self.logger.warning("Content transformation failed",
                                      url=item['url'],
                                      error=result.error_message)
        
        self.logger.info("News transformation completed",
                        total_transformed=len(transformed_data))
        return transformed_data
    
    def load_content(self, transformed_data: List[Dict[str, Any]], content_type: str = "default") -> List[str]:
        """Load transformed content to storage."""
        self.logger.info(f"Starting content loading for {content_type}")
        
        # Convert to ContentItem objects
        content_items = []
        for item in transformed_data:
            content_item = ContentItem(
                content=item['content'],
                metadata=item['metadata'],
                source_url=item['url'],
                content_type="markdown"
            )
            content_items.append(content_item)
        
        # Load using organized structure
        with self.logger.timed_operation("content_loading", item_count=len(content_items)):
            organized_results = self.loader.create_organized_structure(
                content_items,
                Path(self.config.scraping.output.base_directory) / "processed"
            )
        
        # Collect all output paths
        all_output_paths = []
        for content_type_results in organized_results.values():
            for result in content_type_results:
                if result.success and result.output_path:
                    all_output_paths.append(result.output_path)
        
        self.logger.info("Content loading completed",
                        total_loaded=len(all_output_paths))
        return all_output_paths
    
    def run_corporate_pipeline(self) -> Dict[str, Any]:
        """Run the complete corporate content pipeline."""
        self.logger.info("Starting corporate pipeline")
        
        with self.logger.timed_operation("corporate_pipeline"):
            # Extract
            extracted_data = self.extract_corporate_content()
            if not extracted_data:
                return {'success': False, 'message': 'No corporate content extracted'}
            
            # Transform
            transformed_data = self.transform_corporate_content(extracted_data)
            if not transformed_data:
                return {'success': False, 'message': 'No corporate content transformed'}
            
            # Load
            output_paths = self.load_content(transformed_data, "corporate")
        
        result = {
            'success': True,
            'pipeline_type': 'corporate',
            'extracted_count': len(extracted_data),
            'transformed_count': len(transformed_data),
            'loaded_count': len(output_paths),
            'output_paths': output_paths
        }
        
        self.logger.info("Corporate pipeline completed", **result)
        return result
    
    def run_news_pipeline(self) -> Dict[str, Any]:
        """Run the complete news content pipeline."""
        self.logger.info("Starting news pipeline")
        
        with self.logger.timed_operation("news_pipeline"):
            # Extract
            extracted_data, discovered_links = self.extract_news_content()
            if not extracted_data:
                return {'success': False, 'message': 'No news content extracted'}
            
            # Transform
            transformed_data = self.transform_news_content(extracted_data)
            if not transformed_data:
                return {'success': False, 'message': 'No news content transformed'}
            
            # Load
            output_paths = self.load_content(transformed_data, "news")
        
        result = {
            'success': True,
            'pipeline_type': 'news',
            'extracted_count': len(extracted_data),
            'transformed_count': len(transformed_data),
            'loaded_count': len(output_paths),
            'discovered_links_count': len(discovered_links),
            'output_paths': output_paths
        }
        
        self.logger.info("News pipeline completed", **result)
        return result
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run both corporate and news pipelines."""
        self.logger.info("Starting full pipeline")
        
        with self.logger.timed_operation("full_pipeline"):
            corporate_result = self.run_corporate_pipeline()
            news_result = self.run_news_pipeline()
        
        result = {
            'success': corporate_result['success'] and news_result['success'],
            'corporate': corporate_result,
            'news': news_result,
            'total_extracted': corporate_result.get('extracted_count', 0) + news_result.get('extracted_count', 0),
            'total_loaded': corporate_result.get('loaded_count', 0) + news_result.get('loaded_count', 0)
        }
        
        self.logger.info("Full pipeline completed", **result)
        
        # Log final metrics summary
        self.logger.log_metrics_summary()
        
        return result
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and configuration."""
        return {
            'environment': self.config,
            'corporate_urls_configured': len(self.config.scraping.targets.corporate_urls),
            'news_urls_configured': len(self.config.scraping.targets.news_base_urls),
            'output_directory': self.config.scraping.output.base_directory,
            'file_format': self.config.scraping.output.file_format,
            'metrics_summary': self.logger.get_metrics_summary()
        }