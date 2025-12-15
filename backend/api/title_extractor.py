"""
Sistema avançado de extração de TÍTULO de produtos
Tenta extrair o título usando 10+ métodos diferentes
"""
import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import json


class TitleExtractor:
    """Extrator de títulos com múltiplos métodos de busca"""

    # Seletores CSS para buscar título
    CSS_SELECTORS = [
        'h1.pdp-title',
        'h1.product_title',
        'h1.product-title',
        'h1.productTitle',
        'h1[itemprop="name"]',
        'h1.entry-title',
        'h1.product-name',
        'h1.item-title',
        '.product-title h1',
        '.product-name h1',
        '#product-title',
        '#productTitle',
        '.product-info h1',
        '.product-details h1',
        'h1',  # Fallback para qualquer h1
        'h2.product-title',
        'h2.product-name',
    ]

    def __init__(self):
        self.methods_tried = []
        self.title_found = None
        self.method_used = None

    def clean_title(self, title: str) -> Optional[str]:
        """Limpa e valida um título"""
        if not title:
            return None

        # Remove espaços extras
        title = ' '.join(title.split())
        title = title.strip()

        # Ignora títulos muito curtos ou inválidos
        if len(title) < 3:
            return None

        # Ignora títulos genéricos
        generic_titles = [
            'product', 'item', 'untitled', 'sem título', 'no title',
            'loading', 'home', 'homepage', 'página inicial'
        ]
        if title.lower() in generic_titles:
            return None

        return title

    def extract_from_meta_tags(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 1: Extrai de meta tags (og:title, twitter:title, etc)"""
        self.methods_tried.append('meta-tags')

        meta_selectors = [
            ('property', 'og:title'),
            ('name', 'twitter:title'),
            ('property', 'og:product:name'),
            ('name', 'title'),
            ('itemprop', 'name'),
        ]

        for attr, value in meta_selectors:
            meta = soup.find('meta', attrs={attr: value})
            if meta and meta.get('content'):
                title = self.clean_title(meta.get('content'))
                if title:
                    return title

        return None

    def extract_from_h1_tags(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 2: Busca em tags H1 com seletores específicos"""
        self.methods_tried.append('h1-tags')

        for selector in self.CSS_SELECTORS:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    title = self.clean_title(text)
                    if title:
                        return title
            except Exception:
                continue

        return None

    def extract_from_json_ld(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 3: Extrai de JSON-LD (Schema.org)"""
        self.methods_tried.append('json-ld')

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                text = script.string
                if not text:
                    continue

                data = json.loads(text)

                def search_obj(obj):
                    if isinstance(obj, dict):
                        # Busca por chave 'name' (nome do produto)
                        if 'name' in obj and obj.get('@type') in ['Product', 'ProductModel', None]:
                            title = self.clean_title(str(obj['name']))
                            if title:
                                return title

                        # Busca recursiva
                        for value in obj.values():
                            result = search_obj(value)
                            if result:
                                return result

                    elif isinstance(obj, list):
                        for item in obj:
                            result = search_obj(item)
                            if result:
                                return result

                    return None

                result = search_obj(data)
                if result:
                    return result

            except (json.JSONDecodeError, Exception):
                continue

        return None

    def extract_from_title_tag(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 4: Extrai da tag <title>"""
        self.methods_tried.append('title-tag')

        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()

            # Remove partes comuns do título da página
            # Ex: "Product Name - Store Name" -> "Product Name"
            separators = [' - ', ' | ', ' :: ', ' — ', ' – ']
            for sep in separators:
                if sep in title_text:
                    parts = title_text.split(sep)
                    # Pega a primeira parte (geralmente é o nome do produto)
                    title = self.clean_title(parts[0])
                    if title:
                        return title

            # Se não tiver separador, usa o título completo
            title = self.clean_title(title_text)
            if title:
                return title

        return None

    def extract_from_itemprop(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 5: Busca por atributo itemprop="name" """
        self.methods_tried.append('itemprop')

        # Busca elementos com itemprop="name"
        elements = soup.find_all(attrs={'itemprop': 'name'})
        for elem in elements:
            text = elem.get_text(strip=True)
            title = self.clean_title(text)
            if title:
                return title

        return None

    def extract_from_data_attributes(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 6: Busca em atributos data-*"""
        self.methods_tried.append('data-attributes')

        # Atributos data-* comuns para nome de produto
        data_attrs = [
            'data-product-name',
            'data-product-title',
            'data-name',
            'data-title',
            'data-product',
        ]

        for attr in data_attrs:
            elements = soup.find_all(attrs={attr: True})
            for elem in elements:
                value = elem.get(attr)

                # Se for string diretamente
                if isinstance(value, str):
                    title = self.clean_title(value)
                    if title:
                        return title

                # Se for JSON
                if isinstance(value, str) and value.startswith('{'):
                    try:
                        data = json.loads(value)
                        if isinstance(data, dict):
                            for key in ['name', 'title', 'productName']:
                                if key in data:
                                    title = self.clean_title(str(data[key]))
                                    if title:
                                        return title
                    except (json.JSONDecodeError, Exception):
                        continue

        return None

    def extract_from_window_objects(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 7: Busca em objetos window (Next.js, Shopify, etc)"""
        self.methods_tried.append('window-objects')

        for script in soup.find_all('script'):
            text = script.string or ''
            if not text:
                continue

            # Padrões para objetos window
            patterns = [
                r'window\.__NEXT_DATA__\s*=\s*({.+?});',
                r'window\.Shopify\s*=\s*({.+?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'var\s+productData\s*=\s*({.+?});',
                r'const\s+product\s*=\s*({.+?});',
            ]

            for pattern in patterns:
                try:
                    match = re.search(pattern, text, re.I | re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        # Limita o tamanho para evitar problemas
                        if len(json_str) > 500000:
                            continue

                        data = json.loads(json_str)

                        # Busca recursiva por 'name' ou 'title'
                        def search_nested(obj, depth=0):
                            if depth > 8:  # Evita recursão profunda
                                return None

                            if isinstance(obj, dict):
                                # Prioriza campos de produto
                                for key in ['name', 'title', 'productName', 'productTitle']:
                                    if key in obj:
                                        val = obj[key]
                                        if isinstance(val, str):
                                            title = self.clean_title(val)
                                            if title:
                                                return title

                                # Busca recursiva
                                for value in obj.values():
                                    result = search_nested(value, depth + 1)
                                    if result:
                                        return result

                            elif isinstance(obj, list):
                                for item in obj:
                                    result = search_nested(item, depth + 1)
                                    if result:
                                        return result

                            return None

                        result = search_nested(data)
                        if result:
                            return result

                except (json.JSONDecodeError, Exception):
                    continue

        return None

    def extract_from_breadcrumbs(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 8: Extrai o último item do breadcrumb"""
        self.methods_tried.append('breadcrumbs')

        # Seletores comuns de breadcrumb
        breadcrumb_selectors = [
            'nav[aria-label="breadcrumb"] li:last-child',
            '.breadcrumb li:last-child',
            '.breadcrumbs li:last-child',
            '[itemtype="http://schema.org/BreadcrumbList"] [itemprop="name"]:last-of-type',
        ]

        for selector in breadcrumb_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    title = self.clean_title(text)
                    if title:
                        return title
            except Exception:
                continue

        return None

    def extract_from_og_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 9: Tenta extrair do og:description como fallback"""
        self.methods_tried.append('og-description')

        meta = soup.find('meta', property='og:description')
        if meta and meta.get('content'):
            desc = meta.get('content', '')
            # Pega apenas a primeira frase (geralmente contém o nome)
            first_sentence = desc.split('.')[0].strip()
            title = self.clean_title(first_sentence)
            if title and len(title) > 10:  # Só se for razoavelmente longo
                return title

        return None

    def extract_from_largest_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 10: Pega o maior texto em headings (h1-h3)"""
        self.methods_tried.append('largest-heading')

        # Busca todos os headings
        headings = soup.find_all(['h1', 'h2', 'h3'])

        longest_text = ""
        for heading in headings:
            text = heading.get_text(strip=True)
            if len(text) > len(longest_text) and len(text) < 200:  # Não muito longo
                longest_text = text

        title = self.clean_title(longest_text)
        if title:
            return title

        return None

    def extract_all_methods(self, html: str) -> Optional[str]:
        """
        Executa TODOS os métodos de extração em ordem de prioridade
        Retorna o primeiro título válido encontrado
        """
        self.methods_tried = []
        self.title_found = None
        self.method_used = None

        soup = BeautifulSoup(html, 'html.parser')

        # Ordem de prioridade dos métodos
        extraction_methods = [
            self.extract_from_meta_tags,
            self.extract_from_json_ld,
            self.extract_from_h1_tags,
            self.extract_from_itemprop,
            self.extract_from_title_tag,
            self.extract_from_data_attributes,
            self.extract_from_window_objects,
            self.extract_from_breadcrumbs,
            self.extract_from_og_description,
            self.extract_from_largest_text,
        ]

        for method in extraction_methods:
            try:
                result = method(soup)
                if result:
                    self.title_found = result
                    self.method_used = self.methods_tried[-1] if self.methods_tried else 'unknown'
                    return result
            except Exception:
                continue

        return None

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre a extração"""
        return {
            'title_found': self.title_found,
            'method_used': self.method_used,
            'methods_tried': len(self.methods_tried),
            'all_methods': self.methods_tried
        }


# Função auxiliar para compatibilidade
def extract_title_from_html(html: str) -> Optional[str]:
    """
    Função auxiliar que usa o TitleExtractor
    Mantém compatibilidade com código existente
    """
    extractor = TitleExtractor()
    return extractor.extract_all_methods(html)
