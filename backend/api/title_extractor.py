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
        self.additional_info = []  # Armazena Part Number, Model, SKU, etc

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

    def extract_additional_info(self, soup: BeautifulSoup, base_title: str = None) -> List[str]:
        """
        Método NOVO: Extrai informações adicionais como Part Number, Model, SKU, Brand
        que geralmente aparecem abaixo do título do produto

        IMPORTANTE: Foca apenas no contexto próximo ao título principal para evitar
        pegar informações de produtos relacionados/recomendados
        """
        additional_info = []

        # Palavras-chave que indicam informações importantes
        keywords = [
            'part number', 'partnumber', 'part #', 'part no',
            'model', 'model number', 'model #', 'modelo',
            'sku', 'item #', 'item number', 'item no',
            'brand', 'marca', 'manufacturer',
            'product code', 'código', 'reference',
            'upc', 'ean', 'isbn', 'asin',
            'mpn', 'mfr', 'mfg part',
            'scale', 'escala',  # IMPORTANTE: para capturar "Scale: 1:64"
        ]

        # Encontra o container principal do produto (próximo ao título)
        product_container = None
        h1_tag = soup.find('h1')

        if h1_tag:
            # Tenta encontrar o container pai do produto
            # Procura por divs/sections comuns que englobam o produto principal
            for parent in h1_tag.parents:
                if parent.name in ['section', 'div', 'article', 'main']:
                    # Verifica se tem classes que indicam ser o container do produto
                    classes = ' '.join(parent.get('class', [])).lower()
                    if any(kw in classes for kw in ['product', 'item', 'detail', 'pdp', 'main-content']):
                        product_container = parent
                        break

            # Se não achou container específico, usa um escopo limitado ao redor do h1
            if not product_container:
                # Pega apenas os próximos 3 irmãos do h1
                product_container = soup.new_tag('div')
                product_container.append(h1_tag)
                for i, sibling in enumerate(h1_tag.next_siblings):
                    if i >= 10:  # Limita a 10 elementos seguintes
                        break
                    if hasattr(sibling, 'name'):
                        product_container.append(sibling)

        # Se não achou h1, usa todo o soup mas com restrições
        if not product_container:
            product_container = soup

        # 1. Busca em meta tags (PRIORIDADE: pega brand direto das meta tags)
        for meta in soup.find_all('meta'):
            name = (meta.get('name') or meta.get('property') or meta.get('itemprop') or '').lower()
            content = meta.get('content', '').strip()

            if content and len(content) < 100:
                # Brand/Manufacturer em meta tags tem alta prioridade
                if any(kw in name for kw in ['brand', 'manufacturer']):
                    additional_info.append(content)
                # Outras informações úteis
                elif any(kw in name for kw in ['mpn', 'sku', 'gtin', 'model']):
                    additional_info.append(content)

        # 2. Busca em elementos com classes/ids específicos (APENAS no container do produto)
        selectors = [
            '.part-number', '#part-number', '[data-part-number]',
            '.model-number', '#model-number', '[data-model]',
            '.sku', '#sku', '[data-sku]',
            '.product-code', '#product-code',
            '.item-number', '#item-number',
            '.brand-name', '#brand', '[data-brand]',
            '.manufacturer', '[data-manufacturer]',
            '[itemprop="mpn"]', '[itemprop="sku"]', '[itemprop="brand"]',
            '[itemprop="model"]', '[itemprop="productID"]',
        ]

        for selector in selectors:
            try:
                # USA product_container ao invés de soup
                elements = product_container.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    # Também tenta pegar de atributos data-*
                    if not text:
                        for attr in elem.attrs:
                            if attr.startswith('data-'):
                                val = elem.get(attr)
                                if isinstance(val, str) and len(val) < 100:
                                    text = val
                                    break

                    if text and len(text) < 100:
                        additional_info.append(text)
            except Exception:
                continue

        # 3. Busca em textos com padrões "Label: Value" (APENAS no container do produto)
        # Ex: "Part Number: LP64770", "Model: ABC123"
        text_content = product_container.get_text()

        for keyword in keywords:
            # Padrão: "keyword: value" ou "keyword value"
            # IMPORTANTE: Inclui : no padrão de captura para pegar "1:64", "1/32", etc
            patterns = [
                rf'{re.escape(keyword)}\s*:\s*([A-Z0-9\-_#\/:\.]+)',  # Captura até encontrar espaço/quebra
                rf'{re.escape(keyword)}\s+([A-Z0-9\-_#\/:\.]+)',      # Sem dois pontos
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    value = match.group(1).strip()
                    # Remove espaços internos excessivos
                    value = ' '.join(value.split())
                    if len(value) >= 2 and len(value) < 50:
                        additional_info.append(value)

        # 4. Busca em listas de detalhes (dl/dt/dd) - APENAS no container
        for dl in product_container.find_all('dl'):
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')

            for dt, dd in zip(dt_elements, dd_elements):
                label = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)

                if any(kw in label for kw in keywords) and value and len(value) < 100:
                    additional_info.append(value)

        # 5. Busca em tabelas de especificações - APENAS no container
        for table in product_container.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if any(kw in label for kw in keywords) and value and len(value) < 100:
                        additional_info.append(value)

        # 6. Busca SOMENTE no primeiro h1 encontrado (título principal)
        h1_tag = soup.find('h1')  # Pega apenas o PRIMEIRO h1
        if h1_tag:
            # Pega elementos irmãos (siblings) próximos ao h1
            for sibling in list(h1_tag.next_siblings)[:5]:  # Limita a 5 elementos seguintes
                if hasattr(sibling, 'get_text'):
                    text = sibling.get_text(strip=True)

                    # Verifica se contém padrões de informação adicional
                    for keyword in keywords:
                        if keyword in text.lower():
                            # Extrai apenas o valor
                            match = re.search(rf'{re.escape(keyword)}\s*:?\s*([A-Z0-9\-_#\/]+)', text, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                if len(value) >= 3 and len(value) < 50:
                                    additional_info.append(value)
                            # Se não achou padrão, mas o texto é curto, adiciona ele todo
                            elif len(text) < 100 and len(text) > 3:
                                additional_info.append(text)

        # Remove duplicatas e filtra ruído com priorização
        seen = set()
        unique_info = []

        # Palavras para ignorar (muito genéricas ou inúteis)
        ignore_words = {
            'number', 'model', 'brand', 'item', 'part', 'sku', 'code',
            'product', 'manufacturer', 'reference', 'details', 'info'
        }

        # Separa em categorias para priorizar
        part_numbers = []
        brands = []
        models = []
        others = []

        for info in additional_info:
            info_clean = info.strip()

            # Ignora se muito curto ou muito longo
            if len(info_clean) < 2 or len(info_clean) > 80:
                continue

            # Ignora se for apenas uma palavra genérica
            if info_clean.lower() in ignore_words:
                continue

            # Ignora se já foi visto
            if info_clean in seen:
                continue

            seen.add(info_clean)

            # Categoriza a informação
            info_lower = info_clean.lower()

            # Marcas conhecidas de die-cast/brinquedos
            known_brands = [
                'john deere', 'deere',
                'tomy', 'ertl',
                'matchbox', 'hot wheels', 'hotwheels',
                'johnny lightning',
                'maisto', 'greenlight',
                'jada', 'mattel',
                'bruder', 'siku',
                'corgi', 'dinky',
                'autoworld', 'auto world',
                'racing champions',
                'm2 machines',
                'schleich', 'papo'
            ]

            if any(brand in info_lower for brand in known_brands):
                brands.append(info_clean)
            # Modelos/Escala: 1:64, 1/32, "1 64 scale", etc
            elif re.search(r'\d+[:/]\d+|scale.*\d+:\d+|\d+:\d+.*scale', info_lower):
                # Limpa "Scale: " do texto se tiver
                model_clean = re.sub(r'scale\s*:?\s*', '', info_clean, flags=re.I).strip()
                if model_clean:
                    models.append(model_clean)
            # Part Numbers - APENAS para categorizar, NÃO será usado!
            elif re.match(r'^[A-Z]{1,4}\d+[A-Z]?$', info_clean, re.I):
                part_numbers.append(info_clean)
            else:
                others.append(info_clean)

        # NOVA ESTRATÉGIA: Captura APENAS Brand + Modelo
        # IGNORA Part Numbers completamente (não funcionam bem na Amazon)
        result = []

        # 1. Adiciona marca (prioriza "John Deere" completo)
        for brand in brands:
            if 'deere' in brand.lower():
                result.append(brand)
                break
        if not result and brands:
            result.append(brands[0])

        # 2. Adiciona modelo/escala (1:64, 1/32, etc)
        if models:
            result.append(models[0])

        # IMPORTANTE: NÃO adiciona Part Numbers!
        # Part Numbers (LP84525, MB-2024-HVL75) não funcionam na busca da Amazon

        return result[:2]  # Limita a 2 itens: Brand + Modelo

    def extract_all_methods(self, html: str) -> Optional[str]:
        """
        Executa TODOS os métodos de extração em ordem de prioridade
        Retorna o título completo com informações adicionais (Part Number, Model, etc)
        """
        self.methods_tried = []
        self.title_found = None
        self.method_used = None
        self.additional_info = []

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

        # Extrai o título base
        base_title = None
        for method in extraction_methods:
            try:
                result = method(soup)
                if result:
                    base_title = result
                    self.title_found = result
                    self.method_used = self.methods_tried[-1] if self.methods_tried else 'unknown'
                    break
            except Exception:
                continue

        # Se não achou título, retorna None
        if not base_title:
            return None

        # Extrai informações adicionais (Part Number, Model, SKU, etc)
        try:
            additional_info = self.extract_additional_info(soup, base_title)
            self.additional_info = additional_info
        except Exception:
            additional_info = []

        # Combina título com informações adicionais
        if additional_info:
            # Junta as informações adicionais em uma string
            info_str = ' | '.join(additional_info)
            # Retorna: "Título Original | Part Number | Model | etc"
            full_title = f"{base_title} | {info_str}"
            self.title_found = full_title
            return full_title
        else:
            return base_title

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre a extração"""
        return {
            'title_found': self.title_found,
            'method_used': self.method_used,
            'methods_tried': len(self.methods_tried),
            'all_methods': self.methods_tried,
            'additional_info': self.additional_info
        }


# Função auxiliar para compatibilidade
def extract_title_from_html(html: str) -> Optional[str]:
    """
    Função auxiliar que usa o TitleExtractor
    Mantém compatibilidade com código existente
    """
    extractor = TitleExtractor()
    return extractor.extract_all_methods(html)
