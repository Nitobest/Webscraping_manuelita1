import requests
from bs4 import BeautifulSoup
import html2text
import os
import time
import re
from urllib.parse import urlparse, urljoin
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base URLs to scrape
base_urls = [
    "https://www.manuelita.com/manuelita-noticias",
    "https://www.manuelita.com/manuelita-noticias/page/2",
    "https://www.manuelita.com/manuelita-noticias/page/3",
    "https://www.manuelita.com/manuelita-noticias/page/4",
    "https://www.manuelita.com/manuelita-noticias/page/5",
    "https://www.manuelita.com/manuelita-noticias/page/6",
    "https://www.manuelita.com/manuelita-noticias/page/7",
    "https://www.manuelita.com/manuelita-noticias/page/8",
    "https://www.manuelita.com/manuelita-noticias/page/9",
    "https://www.manuelita.com/manuelita-noticias/page/10",
    "https://www.manuelita.com/manuelita-noticias/page/11",
    "https://www.manuelita.com/manuelita-noticias/page/12",
    "https://www.manuelita.com/manuelita-noticias/page/13",
    "https://fundacionmanuelita.org/noticias/",
    "https://fundacionmanuelita.org/",
    "https://www.manuelita.com/manuelita-noticias/manuelita-y-comunidades-vecinas-compromiso-y-confianza-para-el-tejido-social/",
    "https://www.manuelita.com/manuelita-noticias/manuelita-recibe-reconocimiento-por-su-compromiso-social-con-las-comunidades-del-meta/"
]

def get_session():
    """Create a session with proper headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def clean_filename(url):
    """Convert URL to a clean filename"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_').replace('-', '_')
    if not path:
        path = 'home'
    # Limit filename length
    if len(path) > 100:
        path = path[:100]
    return f"{domain}_{path}.md"

def clean_markdown_content(content):
    """Clean and format markdown content"""
    # Remove excessive whitespace and empty lines
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
    
    # Join lines and remove sections with no content
    content = '\n'.join(cleaned_lines)
    
    # Remove empty headers (headers with no content after them)
    content = re.sub(r'^#+\s*$', '', content, flags=re.MULTILINE)
    
    # Remove excessive blank lines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    return content.strip()

def extract_article_links(soup, base_url):
    """Extract individual article links from a news listing page"""
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
                if (('/manuelita-noticias/' in full_url and full_url != base_url and '/page/' not in full_url) or
                    ('/noticias/' in full_url and 'fundacionmanuelita.org' in full_url)):
                    article_links.add(full_url)
    
    return article_links

def scrape_url(session, url):
    """Scrape a single URL and return markdown content and discovered links"""
    try:
        logging.info(f"Scraping: {url}")
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article links if this is a listing page
        article_links = set()
        if ('/manuelita-noticias' in url and '/page/' in url) or url.endswith('/manuelita-noticias') or '/noticias/' in url:
            article_links = extract_article_links(soup, url)
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Remove common unwanted elements
        for element in soup.find_all(class_=['menu', 'navigation', 'sidebar', 'cookie', 'popup', 'social-share']):
            element.decompose()
        
        # Convert to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        
        markdown_content = h.handle(str(soup))
        
        # Clean the content
        cleaned_content = clean_markdown_content(markdown_content)
        
        return cleaned_content, article_links
        
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return f"# Error scraping {url}\n\nError: {str(e)}", set()

def save_discovered_links(all_links):
    """Save all discovered links to a JSON file"""
    links_data = {
        'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_links': len(all_links),
        'links': sorted(list(all_links))
    }
    
    
    with open('discovered_news_links.json', 'w', encoding='utf-8') as f:
        json.dump(links_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved {len(all_links)} discovered links to discovered_news_links.json")

def main():
    """Main function to scrape all URLs and discover sublinks"""
    output_dir = "manuelita_news_content"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    session = get_session()
    all_discovered_links = set()
    scraped_urls = set()
    
    # Remove duplicates while preserving order
    unique_urls = list(dict.fromkeys(base_urls))
    
    logging.info(f"Starting to scrape {len(unique_urls)} base URLs")
    
    # Phase 1: Scrape base URLs and discover article links
    for i, url in enumerate(unique_urls, 1):
        try:
            content, article_links = scrape_url(session, url)
            
            # Save base page content
            filename = clean_filename(url)
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {url}\n\n")
                f.write(content)
            
            logging.info(f"Saved base page: {filename} ({i}/{len(unique_urls)})")
            
            # Add discovered links
            all_discovered_links.update(article_links)
            scraped_urls.add(url)
            
            logging.info(f"Discovered {len(article_links)} article links from {url}")
            
            # Be respectful - add delay between requests
            time.sleep(2)
            
        except Exception as e:
            logging.error(f"Failed to process {url}: {str(e)}")
            continue
    
    # Save discovered links
    save_discovered_links(all_discovered_links)
    
    # Phase 2: Scrape discovered article links
    new_articles = all_discovered_links - scraped_urls
    logging.info(f"Found {len(new_articles)} new article links to scrape")
    
    for i, url in enumerate(new_articles, 1):
        try:
            content, _ = scrape_url(session, url)
            
            # Create filename for article
            filename = clean_filename(url)
            filepath = os.path.join(output_dir, f"article_{filename}")
            
            # Write content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {url}\n\n")
                f.write(content)
            
            logging.info(f"Saved article: article_{filename} ({i}/{len(new_articles)})")
            
            # Be respectful - add delay between requests
            time.sleep(2)
            
        except Exception as e:
            logging.error(f"Failed to process article {url}: {str(e)}")
            continue
    
    # Create summary report
    create_summary_report(output_dir, len(unique_urls), len(new_articles), all_discovered_links)
    
    logging.info("News scraping completed!")

def create_summary_report(output_dir, base_count, article_count, all_links):
    """Create a summary report of the scraping process"""
    summary_content = f"""# Manuelita News Scraping Report

## Summary

- **Base URLs scraped**: {base_count}
- **Individual articles discovered and scraped**: {article_count}
- **Total unique links found**: {len(all_links)}
- **Scraping completed**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Content Structure

### Base News Pages
These pages contain news listings and overviews:
- News index pages (pages 1-13)
- Foundation news pages
- Special announcement pages

### Individual News Articles
Each article has been saved with the prefix "article_" followed by a descriptive filename.

### Files Generated
All content has been saved in the `{output_dir}/` directory with clean markdown formatting.

## Discovered Links
A complete list of discovered links has been saved to `discovered_news_links.json` for reference.

## Notes
- All content has been cleaned and formatted as markdown
- Empty sections and navigation elements have been removed
- Links and images have been preserved where relevant
- Processing included delays to respect server resources
"""
    
    with open(os.path.join(output_dir, 'SCRAPING_REPORT.md'), 'w', encoding='utf-8') as f:
        f.write(summary_content)

if __name__ == "__main__":
    main()