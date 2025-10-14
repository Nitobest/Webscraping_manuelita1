"""
Base Extractor Classes

This module provides base classes for data extraction (scraping) operations.
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from pathlib import Path
import json

from bs4 import BeautifulSoup
import html2text

from ..config import ScrapingConfig
from ..logging_config import get_logger


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    url: str
    content: str
    metadata: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None
    discovered_links: Set[str] = None
    
    def __post_init__(self):
        if self.discovered_links is None:
            self.discovered_links = set()


class BaseExtractor(ABC):
    """Base class for data extractors."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.logger = get_logger()
        self.session = self._create_session()
        self._processed_urls: Set[str] = set()
    
    def _create_session(self) -> requests.Session:
        """Create and configure HTTP session."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config.settings.user_agent
        })
        return session
    
    def _clean_filename(self, url: str) -> str:
        """Convert URL to a clean filename."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        path = parsed.path.strip('/').replace('/', '_').replace('-', '_')
        if not path:
            path = 'home'
        
        # Limit filename length
        if len(path) > 100:
            path = path[:100]
        
        return f"{domain}_{path}.md"
    
    def _should_process_url(self, url: str) -> bool:
        """Check if URL should be processed based on exclusion patterns."""
        if url in self._processed_urls:
            return False
            
        for pattern in self.config.targets.excluded_patterns:
            if pattern.replace('*', '') in url:
                return False
        
        return True
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'scraped_at': time.time()
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Extract meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            metadata['description'] = desc_tag.get('content', '').strip()
        
        # Extract other useful metadata
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title:
            metadata['og_title'] = og_title.get('content', '').strip()
        
        return metadata
    
    def _convert_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert BeautifulSoup object to markdown."""
        # Configure html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        
        return h.handle(str(soup))
    
    def _clean_content(self, content: str) -> str:
        """Basic content cleaning."""
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:
                    cleaned_lines.append('')
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        # Join lines and remove excessive blank lines
        result = '\n'.join(cleaned_lines)
        result = '\n\n'.join(section.strip() for section in result.split('\n\n') if section.strip())
        
        return result.strip()
    
    def extract_single_url(self, url: str) -> ScrapingResult:
        """Extract content from a single URL."""
        if not self._should_process_url(url):
            return ScrapingResult(
                url=url,
                content="",
                metadata={},
                success=False,
                error_message="URL excluded or already processed"
            )
        
        with self.logger.timed_operation("scrape_url", url=url):
            try:
                # Add delay between requests
                if self._processed_urls:  # Not the first request
                    time.sleep(self.config.settings.request_delay)
                
                # Make request
                response = self.session.get(url, timeout=self.config.settings.timeout)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                self._remove_unwanted_elements(soup)
                
                # Extract metadata
                metadata = self._extract_metadata(soup, url)
                
                # Convert to markdown
                markdown_content = self._convert_to_markdown(soup)
                
                # Clean content
                cleaned_content = self._clean_content(markdown_content)
                
                # Discover additional links if applicable
                discovered_links = self._discover_links(soup, url)
                
                self._processed_urls.add(url)
                
                return ScrapingResult(
                    url=url,
                    content=cleaned_content,
                    metadata=metadata,
                    success=True,
                    discovered_links=discovered_links
                )
                
            except Exception as e:
                self.logger.error(f"Failed to scrape URL: {url}", error=e, url=url)
                return ScrapingResult(
                    url=url,
                    content="",
                    metadata={'url': url, 'scraped_at': time.time()},
                    success=False,
                    error_message=str(e)
                )
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted HTML elements."""
        # Remove script, style, navigation elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Remove elements with common unwanted classes
        unwanted_classes = ['menu', 'navigation', 'sidebar', 'cookie', 'popup', 'social-share']
        for class_name in unwanted_classes:
            for element in soup.find_all(class_=class_name):
                element.decompose()
    
    @abstractmethod
    def _discover_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Discover additional links from the page. To be implemented by subclasses."""
        pass
    
    @abstractmethod
    def extract_multiple_urls(self, urls: List[str]) -> List[ScrapingResult]:
        """Extract content from multiple URLs. To be implemented by subclasses."""
        pass
    
    def save_result(self, result: ScrapingResult, output_dir: str) -> Optional[Path]:
        """Save scraping result to file."""
        if not result.success or not result.content.strip():
            self.logger.warning(f"Skipping save for failed/empty result: {result.url}")
            return None
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = self._clean_filename(result.url)
        filepath = output_path / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if self.config.output.include_metadata:
                    f.write(f"# {result.url}\n\n")
                    if result.metadata.get('title'):
                        f.write(f"**Title:** {result.metadata['title']}\n\n")
                f.write(result.content)
            
            self.logger.info(f"Saved content to {filepath}", url=result.url, filepath=str(filepath))
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save content for {result.url}", error=e)
            return None
    
    def save_discovered_links(self, all_links: Set[str], output_file: str) -> None:
        """Save discovered links to JSON file."""
        links_data = {
            'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_links': len(all_links),
            'links': sorted(list(all_links))
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(links_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(all_links)} discovered links", 
                           output_file=output_file, total_links=len(all_links))
                           
        except Exception as e:
            self.logger.error("Failed to save discovered links", error=e, output_file=output_file)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processing."""
        return {
            'total_processed': len(self._processed_urls),
            'processed_urls': list(self._processed_urls)
        }