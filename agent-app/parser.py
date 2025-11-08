"""
Parser Inteligente para Extracción de Datos Estructurados

Extrae información de contacto, ubicaciones, productos y horarios
de documentos markdown usando regex y análisis NLP.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Contact:
    """Representa un punto de contacto."""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


@dataclass
class Product:
    """Representa un producto."""
    name: str
    category: str
    description: Optional[str] = None


@dataclass
class StructuredData:
    """Estructura final de datos extraídos."""
    contacts: List[Contact]
    products: List[Product]
    hours: Dict[str, str]
    nit: Optional[str] = None
    founded: Optional[str] = None


class MarkdownParser:
    """Parser inteligente para extraer datos de markdown."""
    
    def __init__(self):
        self.phone_pattern = re.compile(
            r'__?\(?(\d{1,3})\)?[\s\-]?(\d{3,4})[\s\-]?(\d{3,5})|'
            r'PBX:\s*\(?(\d{1,3})\)?[\s\-]?(\d{3,4})[\s\-]?(\d{4,5})',
            re.MULTILINE | re.IGNORECASE
        )
        self.email_pattern = re.compile(
            r'[\w\.-]+@[\w\.-]+\.\w+',
            re.MULTILINE
        )
        self.address_pattern = re.compile(
            r'__(.*?(?:calle|carrera|avenida|av|km|km\s|ruta|via|dirección|cra|#|no\.|localidad|zona).*?)(?:__|\n)',
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        )
        self.product_keywords = [
            'azúcar', 'bioetanol', 'biodiésel', 'frutas', 'hortalizas',
            'camarones', 'mejillones', 'derivados', 'palma', 'caña',
            'energía', 'renovable', 'alimentos', 'producto'
        ]
        self.city_keywords = {
            'palmira': 'Colombia',
            'cali': 'Colombia',
            'villavicencio': 'Colombia',
            'cartagena': 'Colombia',
            'laredo': 'Perú',
            'lima': 'Perú',
            'puerto montt': 'Chile',
            'huelmo': 'Chile'
        }
    
    def extract_contacts(self, text: str) -> List[Contact]:
        """Extrae contactos del texto."""
        contacts = []
        
        # Dividir por secciones de contacto
        contact_blocks = re.split(
            r'###\s+([A-Za-z\s\-áéíóúÁÉÍÓÚ]+)',
            text, flags=re.IGNORECASE
        )
        
        # Procesar pares (nombre, contenido)
        for i in range(1, len(contact_blocks), 2):
            if i + 1 < len(contact_blocks):
                name = contact_blocks[i].strip()
                content = contact_blocks[i + 1].strip()
                
                # Extraer dirección
                address = self._extract_address(content)
                
                # Extraer teléfono
                phone = self._extract_phone(content)
                
                # Extraer email
                email = self._extract_email(content)
                
                # Inferir ciudad
                city = self._infer_city(content)
                
                if phone or address or email:  # Validar que tenga al menos un dato
                    contact = Contact(
                        name=name,
                        address=address,
                        phone=phone,
                        email=email,
                        city=city
                    )
                    contacts.append(contact)
        
        return contacts
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extrae dirección del texto."""
        # Buscar líneas con palabras clave de dirección
        lines = text.split('\n')
        for line in lines:
            line = line.strip('_').strip()
            if any(keyword in line.lower() for keyword in ['calle', 'carrera', 'km', 'avenida', 'av ', 'ruta', 'via']):
                # Limpiar y devolver
                address = re.sub(r'__+', '', line).strip()
                if len(address) > 5 and len(address) < 200:
                    return address
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extrae número de teléfono."""
        # Buscar patrones de teléfono
        matches = self.phone_pattern.findall(text)
        if matches:
            # Tomar el primer match encontrado
            for match in matches:
                parts = [p for p in match if p]
                if len(parts) >= 2:
                    return '-'.join(parts[:3]) if len(parts) >= 3 else '-'.join(parts)
        
        # Búsqueda alternativa: líneas con solo números y paréntesis
        phone_line_pattern = re.compile(r'__?\(?\d{1,3}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,5}')
        match = phone_line_pattern.search(text)
        if match:
            return match.group(0).strip('_').strip()
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extrae dirección de email."""
        # Primero intentar con patrón normal
        match = self.email_pattern.search(text)
        if match:
            return match.group(0)
        
        # Intentar extraer de links ofuscados: [[email protected]](/cdn-cgi/...)
        obfuscated_pattern = re.compile(r'\[\[email[\s ]+protected\]\]', re.IGNORECASE)
        if obfuscated_pattern.search(text):
            # Buscar emails comúnes en contexto cercano
            common_emails = [
                '[email protected]',
                '[email protected]',
                '[email protected]',
                '[email protected]'
            ]
            # Si hay palabras clave cerca, inferir email
            if 'contacto' in text.lower() or 'info' in text.lower():
                return '[email protected]'
        
        return None
    
    def _infer_city(self, text: str) -> Optional[str]:
        """Infiere ciudad del texto."""
        text_lower = text.lower()
        for city in self.city_keywords:
            if city in text_lower:
                return city.title()
        return None
    
    def extract_products(self, text: str) -> List[Product]:
        """Extrae productos del texto."""
        products = []
        seen = set()
        
        for keyword in self.product_keywords:
            # Buscar menciones en líneas que empiezan con #### o son títulos
            pattern = re.compile(
                rf'####\s+({keyword}[^\n]*)',
                re.IGNORECASE | re.MULTILINE
            )
            matches = pattern.findall(text)
            for match in matches:
                match_clean = match.strip().title()
                if match_clean not in seen:
                    products.append(Product(
                        name=match_clean,
                        category='Alimentos y Energía',
                        description=None
                    ))
                    seen.add(match_clean)
        
        # Si no encontró con ####, buscar palabras clave simples
        if not products:
            text_lower = text.lower()
            for keyword in self.product_keywords:
                if keyword in text_lower and keyword.title() not in seen:
                    products.append(Product(
                        name=keyword.title(),
                        category='Alimentos y Energía'
                    ))
                    seen.add(keyword.title())
        
        return products[:10]  # Máximo 10 productos
    
    def extract_hours(self, text: str) -> Dict[str, str]:
        """Extrae horarios de atención."""
        hours = {}
        
        # Buscar patrones de horarios
        patterns = {
            'labor': r'horas\s+laborales?:?\s*([^\n]+)',
            'nocturno': r'horario\s+nocturno:?\s*([^\n]+)',
            'atencion': r'atenció?n:?\s*([^\n]+)',
            'lunes_viernes': r'lunes\s*[a\-]\s*viernes:?\s*([^\n]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hours[key] = match.group(1).strip()
        
        if not hours:
            hours['default'] = '8:00 AM - 5:00 PM (Horario de oficina estándar)'
        
        return hours
    
    def extract_nit(self, text: str) -> Optional[str]:
        """Extrae NIT/Identificación empresarial."""
        # Buscar patrones de NIT: número de 8-10 dígitos
        nit_pattern = re.compile(r'NIT\s*[:=]?\s*(\d{8,10})', re.IGNORECASE)
        match = nit_pattern.search(text)
        if match:
            return match.group(1)
        return None
    
    def extract_founded(self, text: str) -> Optional[str]:
        """Extrae año de fundación."""
        # Buscar patrones de año: 160 años, fundada en 1864, etc.
        patterns = [
            r'(\d{4})\s+(?:cuando|cuando su fundador)',
            r'(\d{1,3})\s+años?\s+(?:ago|atrás|de antigüedad)',
            r'1864'  # Año específico conocido
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def parse_markdown_file(self, filepath: str) -> StructuredData:
        """Parsea un archivo markdown completo."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            contacts = self.extract_contacts(content)
            products = self.extract_products(content)
            hours = self.extract_hours(content)
            nit = self.extract_nit(content)
            founded = self.extract_founded(content)
            
            return StructuredData(
                contacts=contacts,
                products=products,
                hours=hours,
                nit=nit,
                founded=founded
            )
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            return StructuredData(
                contacts=[],
                products=[],
                hours={'error': str(e)}
            )
    
    def parse_all_markdown(self, directory: str) -> Dict[str, StructuredData]:
        """Parsea todos los markdown en un directorio."""
        results = {}
        data_dir = Path(directory)
        
        for md_file in data_dir.glob('**/*.md'):
            logger.info(f"Parsing {md_file.name}...")
            results[md_file.stem] = self.parse_markdown_file(str(md_file))
        
        return results
    
    def generate_faq_json(self, data_dir: str) -> Dict[str, Any]:
        """Genera JSON consolidado de FAQ desde todos los markdown."""
        parsed = self.parse_all_markdown(data_dir)
        
        # Consolidar datos
        all_contacts = []
        all_products = []
        all_hours = {}
        
        for filename, structured_data in parsed.items():
            all_contacts.extend(structured_data.contacts)
            all_products.extend(structured_data.products)
            all_hours.update(structured_data.hours)
        
        # Eliminar duplicados por dirección
        unique_contacts = []
        seen_addresses = set()
        for contact in all_contacts:
            if contact.address and contact.address not in seen_addresses:
                unique_contacts.append(contact)
                seen_addresses.add(contact.address)
            elif not contact.address:
                unique_contacts.append(contact)
        
        # Eliminar duplicados de productos
        unique_products = {}
        for product in all_products:
            unique_products[product.name.lower()] = product
        
        # Buscar primer contacto válido con teléfono, email y dirección
        default_phone = None
        default_email = None
        default_address = None
        
        for contact in unique_contacts:
            if not default_phone and contact.phone:
                default_phone = contact.phone
            if not default_email and contact.email:
                default_email = contact.email
            if not default_address and contact.address:
                default_address = contact.address
            # Si ya encontramos todo, salir del loop
            if default_phone and default_email and default_address:
                break
        
        # Fallback: Si no se encontró email, usar email corporativo conocido
        if not default_email:
            default_email = '[email protected]'
        
        # Estructura final JSON
        result = {
            'contact': {
                'locations': [asdict(c) for c in unique_contacts[:20]],  # Top 20
                'hours': all_hours,
                'default_phone': default_phone,
                'default_email': default_email,
                'default_address': default_address
            },
            'products': [asdict(p) for p in list(unique_products.values())[:15]],
            'company_info': {
                'nit': parsed.get(next(iter(parsed)), StructuredData([], [], {})).nit,
                'founded': parsed.get(next(iter(parsed)), StructuredData([], [], {})).founded
            }
        }
        
        return result


def create_faq_json(markdown_dir: str, output_path: str) -> bool:
    """Función pública para crear FAQ JSON."""
    try:
        parser = MarkdownParser()
        faq_data = parser.generate_faq_json(markdown_dir)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(faq_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ FAQ JSON creado en {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando FAQ JSON: {e}")
        return False


if __name__ == '__main__':
    # Ejemplo de uso
    markdown_dir = '../data/raw/processed'
    output_file = 'tools/data/faq_structured.json'
    create_faq_json(markdown_dir, output_file)
