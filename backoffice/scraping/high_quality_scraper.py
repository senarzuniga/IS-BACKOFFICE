import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
import re
import hashlib
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HighQualityImageScraper:
    """
    Agente especializado en scraping de imágenes de alta calidad
    Optimizado para webs corporativas como INGECART
    """
    
    # Patrones de alta calidad en URLs
    HIGH_QUALITY_PATTERNS = [
        r'large', r'highres', r'original', r'full', r'hd',
        r'\d{3,}x\d{3,}', r'-\d+x\d+', r'1920w', r'1280w'
    ]
    
    # Mínimos para considerar "calidad profesional"
    MIN_DIMENSIONS = {
        'banner': (1920, 500),
        'product': (800, 600),
        'logo': (200, 200),
        'background': (1920, 1080),
        'default': (800, 600)
    }
    
    def __init__(self, output_dir: str = "scraped_images"):
        self.output_dir = output_dir
        self.session = self._create_session()
        self.cache = {}
        self.stats = {
            'total_found': 0,
            'downloaded': 0,
            'failed': 0,
            'filtered_out': 0
        }
        
    def _create_session(self) -> requests.Session:
        """Crea sesión HTTP con headers realistas"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
        })
        return session
    
    def scrape_website(self, url: str, 
                      min_width: int = 800,
                      recursive: bool = False,
                      max_pages: int = 5,
                      progress_callback: Optional[Callable] = None) -> Dict:
        """
        Punto principal de entrada para scraping de una web
        
        Args:
            url: URL a scrapear
            min_width: Ancho mínimo en píxeles
            recursive: Si debe seguir enlaces internos
            max_pages: Máximo de páginas a scrapear (si recursive=True)
            progress_callback: Función para reportar progreso
        """
        
        self.stats = {'total_found': 0, 'downloaded': 0, 'failed': 0, 'filtered_out': 0}
        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'images': [],
            'stats': self.stats,
            'pages_scraped': []
        }
        
        # Lista de URLs a procesar
        urls_to_scrape = [url]
        if recursive:
            internal_links = self._get_internal_links(url)
            urls_to_scrape.extend(internal_links[:max_pages-1])
        
        if progress_callback:
            progress_callback(f"🔍 Analizando {len(urls_to_scrape)} páginas...")
        
        for page_url in urls_to_scrape:
            if progress_callback:
                progress_callback(f"📄 Procesando: {page_url}")
            
            page_images = self._scrape_page(page_url, min_width)
            results['images'].extend(page_images)
            results['pages_scraped'].append(page_url)
            
            if progress_callback:
                self.stats['total_found'] += len(page_images)
                progress_callback(f"   → Encontradas {len(page_images)} imágenes en esta página")
        
        if progress_callback:
            progress_callback(f"✅ Total: {self.stats['total_found']} imágenes encontradas, {self.stats['downloaded']} descargadas")
        
        return results
    
    def _scrape_page(self, url: str, min_width: int) -> List[Dict]:
        """Scrapea una página individual"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            images_data = []
            
            for img in soup.find_all('img'):
                # Extraer URL de alta resolución
                img_url = self._extract_high_res_url(img, url)
                if not img_url:
                    continue
                
                # Analizar calidad potencial antes de descargar
                quality_score = self._assess_quality_potential(img_url, img)
                
                if quality_score >= 3:  # Solo candidatos de calidad media-alta
                    img_info = {
                        'url': img_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'quality_score': quality_score,
                        'source_page': url
                    }
                    images_data.append(img_info)
            
            return images_data
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []
    
    def _extract_high_res_url(self, img_tag, base_url: str) -> Optional[str]:
        """Extrae la URL de mayor resolución disponible"""
        
        # Prioridad: srcset > data-srcset > src > data-src
        srcset = img_tag.get('srcset') or img_tag.get('data-srcset')
        if srcset:
            # Parsear srcset y tomar la URL con mayor resolución
            urls_with_width = []
            for entry in srcset.split(','):
                parts = entry.strip().split(' ')
                if len(parts) >= 2:
                    url_candidate = parts[0]
                    descriptor = parts[1]
                    if descriptor.endswith('w'):
                        try:
                            width = int(descriptor[:-1])
                            urls_with_width.append((width, url_candidate))
                        except:
                            pass
            
            if urls_with_width:
                urls_with_width.sort(reverse=True)
                return urljoin(base_url, urls_with_width[0][1])
        
        # Fallback a src normal
        src = img_tag.get('src') or img_tag.get('data-src')
        if src:
            return urljoin(base_url, src)
        
        return None
    
    def _assess_quality_potential(self, url: str, img_tag) -> int:
        """Evalúa calidad potencial sin descargar (score 0-5)"""
        score = 0
        url_lower = url.lower()
        
        # +2 por patrones de alta calidad
        for pattern in self.HIGH_QUALITY_PATTERNS:
            if re.search(pattern, url_lower):
                score += 2
                break
        
        # +1 por extensiones de alta calidad
        if url_lower.endswith(('.png', '.webp')):
            score += 1
        
        # +1 por presencia de alt text descriptivo
        alt = img_tag.get('alt', '')
        if len(alt) > 20:
            score += 1
        
        # +1 por clase CSS que indica imagen importante
        classes = img_tag.get('class', [])
        if any(c in str(classes).lower() for c in ['hero', 'banner', 'main', 'featured']):
            score += 1
        
        return min(score, 5)
    
    def download_images(self, images_data: List[Dict], 
                       max_images: int = 50,
                       progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Descarga las imágenes con validación de calidad"""
        
        downloaded = []
        
        for idx, img_info in enumerate(images_data[:max_images]):
            if progress_callback:
                progress_callback(f"⬇️ Descargando {idx+1}/{min(len(images_data), max_images)}: {os.path.basename(img_info['url'][:50])}")
            
            result = self._download_single_image(img_info)
            if result:
                downloaded.append(result)
                self.stats['downloaded'] += 1
            else:
                self.stats['failed'] += 1
        
        return downloaded
    
    def _download_single_image(self, img_info: Dict) -> Optional[Dict]:
        """Descarga y valida una imagen individual"""
        try:
            url = img_info['url']
            
            # Verificar caché
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_path = os.path.join(self.output_dir, 'cache', f"{url_hash}.json")
            
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    return json.load(f)
            
            # Descargar
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Validar tamaño
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) < 15000:  # <15KB es muy pequeño
                self.stats['filtered_out'] += 1
                return None
            
            # Validar dimensiones reales
            img_data = BytesIO(response.content)
            with Image.open(img_data) as img:
                width, height = img.size
                
                # Verificar dimensiones mínimas
                if width < 800 and height < 600:
                    self.stats['filtered_out'] += 1
                    return None
                
                # Generar nombre de archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{width}x{height}_{url_hash[:8]}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                
                # Guardar con alta calidad
                os.makedirs(self.output_dir, exist_ok=True)
                img.save(filepath, quality=95, optimize=True)
                
                result = {
                    'filename': filename,
                    'filepath': filepath,
                    'url': url,
                    'width': width,
                    'height': height,
                    'size_kb': len(response.content) / 1024,
                    'alt': img_info.get('alt', ''),
                    'source_page': img_info.get('source_page', ''),
                    'quality_score': img_info.get('quality_score', 0),
                    'downloaded_at': datetime.now().isoformat()
                }
                
                # Guardar en caché
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'w') as f:
                    json.dump(result, f)
                
                return result
                
        except Exception as e:
            logger.error(f"Error downloading {img_info.get('url', 'unknown')}: {e}")
            return None
    
    def _get_internal_links(self, url: str) -> List[str]:
        """Extrae enlaces internos de una página"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            base_domain = urlparse(url).netloc
            
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(url, href)
                if urlparse(full_url).netloc == base_domain:
                    if full_url not in links and full_url != url:
                        links.append(full_url)
            
            return links[:50]  # Limitar para no sobrecargar
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []

# Instancia global
scraper = HighQualityImageScraper()
