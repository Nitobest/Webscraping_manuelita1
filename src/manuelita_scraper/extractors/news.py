"""
News Content Extractor

Specialized extractor for Manuelita news pages with automatic link discovery.
"""

from typing import List, Set
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor, ScrapingResult


class NewsExtractor(BaseExtractor):
    """Extractor specialized for news content with automatic link discovery."""
    
    def _discover_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """
        Discover individual article links from news listing pages.
        """
        article_links = set()
        
        # Common selectors for article links
        selectors = [
            'a[href*="/manuelita-noticias/"]',
            'a[href*="/noticias/"]',
            '.post-title a',
            '.entry-title a',
            'h2 a',
            'h3 a',
            '.news-item a',
            '.article-link'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, href)
                    
                    # Filter for actual article URLs
                    if self._is_article_url(full_url, base_url):
                        article_links.add(full_url)
        
        return article_links
    
    def _is_article_url(self, url: str, base_url: str) -> bool:
        """Check if a URL is likely an article URL."""
        # Include Manuelita news URLs
        if '/manuelita-noticias/' in url and url != base_url and '/page/' not in url:
            return True
            
        # Include foundation news URLs
        if '/noticias/' in url and 'fundacionmanuelita.org' in url:
            return True
            
        return False
    
    def extract_multiple_urls(self, urls: List[str]) -> List[ScrapingResult]:
        """Extract content from multiple news URLs with two-phase processing."""
        results = []
        all_discovered_links = set()
        
        self.logger.info(f"Starting Phase 1: Extracting {len(urls)} base news URLs")
        
        # Phase 1: Extract base URLs and discover article links
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing base news URL {i}/{len(urls)}", url=url)
            
            result = self.extract_single_url(url)
            results.append(result)
            
            if result.success:
                # Collect discovered links
                all_discovered_links.update(result.discovered_links)
                self.logger.increment_counter('news_base_pages_extracted')
            else:
                self.logger.increment_counter('news_base_pages_failed')
        
        self.logger.info(f"Phase 1 completed. Discovered {len(all_discovered_links)} article links")
        
        # Phase 2: Extract discovered article URLs
        if all_discovered_links:
            self.logger.info(f"Starting Phase 2: Extracting {len(all_discovered_links)} discovered articles")
            
            for i, article_url in enumerate(sorted(all_discovered_links), 1):
                if not self._should_process_url(article_url):
                    continue
                    
                self.logger.info(f"Processing article {i}/{len(all_discovered_links)}", url=article_url)
                
                result = self.extract_single_url(article_url)
                results.append(result)
                
                if result.success:
                    self.logger.increment_counter('news_articles_extracted')
                else:
                    self.logger.increment_counter('news_articles_failed')
        
        total_successful = sum(1 for r in results if r.success)
        self.logger.info(f"News extraction completed", 
                        total_urls=len(results), 
                        base_urls=len(urls),
                        discovered_articles=len(all_discovered_links),
                        successful=total_successful)
        
        return results
    
    def extract_and_save_with_discovery(self, base_urls: List[str], output_dir: str, 
                                      links_file: str = "discovered_news_links.json") -> tuple[List[str], Set[str]]:
        """
        Extract news content with link discovery and save results.
        
        Returns:
            Tuple of (saved file paths, discovered links)
        """
        results = self.extract_multiple_urls(base_urls)
        saved_files = []
        all_discovered_links = set()
        
        # Save results and collect discovered links
        for result in results:
            if result.success:
                filepath = self.save_result(result, output_dir)
                if filepath:
                    saved_files.append(str(filepath))
                
                # Collect all discovered links
                all_discovered_links.update(result.discovered_links)
        
        # Save discovered links to JSON file
        if all_discovered_links:
            self.save_discovered_links(all_discovered_links, links_file)
        
        return saved_files, all_discovered_links
    
    def extract_articles_only(self, article_urls: List[str]) -> List[ScrapingResult]:
        """Extract content from a list of specific article URLs."""
        results = []
        
        self.logger.info(f"Extracting {len(article_urls)} specific article URLs")
        
        for i, url in enumerate(article_urls, 1):
            self.logger.info(f"Processing article {i}/{len(article_urls)}", url=url)
            
            result = self.extract_single_url(url)
            results.append(result)
            
            if result.success:
                self.logger.increment_counter('specific_articles_extracted')
            else:
                self.logger.increment_counter('specific_articles_failed')
        
        successful = sum(1 for r in results if r.success)
        self.logger.info(f"Article extraction completed", 
                        total_articles=len(article_urls), 
                        successful=successful)
        
        return results