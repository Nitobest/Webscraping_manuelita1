import requests
from bs4 import BeautifulSoup
import html2text
import os
import time
import re
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of URLs to scrape
urls = [
    "https://www.manuelita.com",
    "https://www.manuelita.com/perfil-corporativo/",
    "https://www.manuelita.com/historia/",
    "https://www.manuelita.com/gobierno-corporativo/",
    "https://www.manuelita.com/plataformas-de-negocios/",
    "https://www.manuelita.com/estrategia-corporativa/",
    "https://www.manuelita.com/linea-etica/",
    "https://www.manuelita.com/proveedores-cana/",
    "https://www.manuelita.com/azucar/",
    "https://www.manuelitaindustria.com/",
    "https://www.manuelita.com/manuelita-productos/energias-renovables/",
    "https://www.manuelita.com/manuelita-productos/derivados-de-la-cana/",
    "https://www.manuelita.com/manuelita-productos/derivados-de-palma/",
    "https://www.manuelita.com/manuelita-productos/frutas-y-hortalizas/",
    "https://www.manuelita.com/manuelita-productos/mejillones/",
    "https://www.manuelita.com/manuelita-productos/camarones/",
    "https://www.manuelita.com/sostenibilidad/",
    "https://www.manuelita.com/talento/",
    "https://www.manuelita.com/manuelita-noticias/",
    "https://www.manuelita.com/blog/",
    "http://fundacionmanuelita.org",
    "http://www.valleonline.org/",
    "https://www.manuelita.com/manuelita-160/",
    "https://www.manuelita.com/contacto/",
    "https://www.manuelita.com/manuelita-productos/azucar-y-endulzantes/",
    "https://www.manuelita.com/manuelita-productos/azucar-industrial/",
    "https://www.manuelita.com/fundacion-manuelita/",
    "https://www.manuelita.com/manuelita-sostenib/ambiental/",
    "https://www.manuelita.com/manuelita-productos/bioetanol/",
    "https://www.manuelita.com/manuelita-productos/biodiesel/",
    "https://www.manuelita.com/manuelita-sostenib/economico/",
    "https://www.manuelita.com/manuelita-sostenib/social/",
    "https://www.manuelita.com/manuelita-noticias/manuelita-160-anos-comprometida-con-un-futuro-sostenible/",
    "https://www.manuelita.com/alimenticio/",
    "https://www.manuelita.com/energetico/",
    "https://www.manuelita.com/otros/",
    "https://www.manuelita.com/aviso-autorizacion-tratamiento-datos-personales/",
    "https://www.manuelita.com/sagrilaft-2/",
    "https://www.manuelita.com/ptee-2/"
]

def clean_filename(url):
    """Convert URL to a clean filename"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_').replace('-', '_')
    if not path:
        path = 'home'
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

def scrape_url(url):
    """Scrape a single URL and return markdown content"""
    try:
        logging.info(f"Scraping: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Remove common unwanted elements
        for element in soup.find_all(class_=['menu', 'navigation', 'sidebar', 'cookie', 'popup']):
            element.decompose()
        
        # Convert to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        
        markdown_content = h.handle(str(soup))
        
        # Clean the content
        cleaned_content = clean_markdown_content(markdown_content)
        
        return cleaned_content
        
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return f"# Error scraping {url}\n\nError: {str(e)}"

def main():
    """Main function to scrape all URLs"""
    output_dir = "manuelita_content"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Remove duplicates while preserving order
    unique_urls = list(dict.fromkeys(urls))
    
    logging.info(f"Starting to scrape {len(unique_urls)} unique URLs")
    
    for i, url in enumerate(unique_urls, 1):
        try:
            content = scrape_url(url)
            
            # Create filename
            filename = clean_filename(url)
            filepath = os.path.join(output_dir, filename)
            
            # Write content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {url}\n\n")
                f.write(content)
            
            logging.info(f"Saved: {filename} ({i}/{len(unique_urls)})")
            
            # Be respectful - add delay between requests
            time.sleep(2)
            
        except Exception as e:
            logging.error(f"Failed to process {url}: {str(e)}")
            continue
    
    logging.info("Scraping completed!")

if __name__ == "__main__":
    main()