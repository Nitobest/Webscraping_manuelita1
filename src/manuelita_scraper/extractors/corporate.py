"""
Corporate Content Extractor

Specialized extractor for Manuelita corporate pages.
"""

from typing import List, Set
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor, ScrapingResult


class CorporateExtractor(BaseExtractor):
    """Extractor specialized for corporate content pages."""
    
    def _discover_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """
        Discover additional corporate links from the page.
        Corporate pages typically don't have dynamic link discovery.
        """
        discovered = set()
        
        # Look for internal corporate links
        selectors = [
            'a[href*="/perfil-corporativo"]',
            'a[href*="/gobierno-corporativo"]',
            'a[href*="/estrategia-corporativa"]',
            'a[href*="/sostenibilidad"]',
            'a[href*="/productos"]',
            'a[href*="/talento"]'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Only add if it's a manuelita.com URL
                    if 'manuelita.com' in full_url:
                        discovered.add(full_url)
        
        return discovered
    
    def extract_multiple_urls(self, urls: List[str]) -> List[ScrapingResult]:
        """Extract content from multiple corporate URLs."""
        results = []
        
        self.logger.info(f"Starting extraction of {len(urls)} corporate URLs")
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing corporate URL {i}/{len(urls)}", url=url)
            
            result = self.extract_single_url(url)
            results.append(result)
            
            if result.success:
                self.logger.increment_counter('corporate_pages_extracted')
            else:
                self.logger.increment_counter('corporate_pages_failed')
        
        self.logger.info(f"Completed corporate extraction", 
                        total_urls=len(urls), 
                        successful=sum(1 for r in results if r.success))
        
        return results
    
    def extract_and_save(self, urls: List[str], output_dir: str) -> List[str]:
        """
        Extract corporate content and save to files.
        
        Returns:
            List of saved file paths
        """
        results = self.extract_multiple_urls(urls)
        saved_files = []
        
        for result in results:
            if result.success:
                filepath = self.save_result(result, output_dir)
                if filepath:
                    saved_files.append(str(filepath))
        
        return saved_files