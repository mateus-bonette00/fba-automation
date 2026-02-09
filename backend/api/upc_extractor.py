"""
Sistema avançado de extração de UPC com múltiplos métodos
Tenta extrair UPC de produtos usando 15+ métodos diferentes
"""
import re
import json
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup


class UPCExtractor:
    """Extrator de UPC com múltiplos métodos de busca"""

    # Padrões regex para encontrar UPC/GTIN
    PATTERNS = {
        'json_key': re.compile(r'"(?:barcode|gtin|gtin12|gtin13|gtin14|upc|ean|ean13)"\s*:\s*"?(\d{8,14})"?', re.I),
        'js_var': re.compile(r'(?:barcode|gtin|upc|ean)\s*[:=]\s*["\']?(\d{8,14})["\']?', re.I),
        'labeled_text': re.compile(r'(?:UPC|GTIN-?1[2-4]|GTIN|Barcode|EAN|Item\s*#|Product\s*Code)\s*[:|\-]?\s*(\d{8,14})', re.I),
        'meta_content': re.compile(r'(\d{12,14})', re.I),
        'window_obj': re.compile(r'window\[?["\']?(?:product|item|data)["\']?\]?\s*=\s*({.+?});', re.I | re.DOTALL),
        'shopify': re.compile(r'"barcode"\s*:\s*"(\d{8,14})"', re.I),
        'woocommerce': re.compile(r'data-product_sku\s*=\s*"(\d{8,14})"', re.I),
        'numeric_12': re.compile(r'\b(\d{12})\b'),
        'numeric_13': re.compile(r'\b(\d{13})\b'),
        'numeric_14': re.compile(r'\b(\d{14})\b'),
    }

    # Seletores CSS para buscar UPC
    CSS_SELECTORS = [
        '[itemprop="gtin"]', '[itemprop="gtin12"]', '[itemprop="gtin13"]', '[itemprop="gtin14"]',
        '[itemprop="sku"]', '[itemprop="productID"]',
        '[data-upc]', '[data-gtin]', '[data-gtin12]', '[data-gtin13]', '[data-gtin14]',
        '[data-barcode]', '[data-ean]', '[data-sku]',
        '.product-upc', '.product-gtin', '.product-barcode', '.product-ean',
        '#upc', '#gtin', '#barcode', '#ean',
        'meta[property="product:upc"]', 'meta[property="product:gtin"]',
        'meta[name="upc"]', 'meta[name="gtin"]', 'meta[name="barcode"]',
        'span.upc', 'span.gtin', 'span.barcode', 'div.upc', 'div.gtin',
        '.product-details-upc', '.product-info-upc',
        '[class*="upc"]', '[class*="gtin"]', '[class*="barcode"]',
        '[id*="upc"]', '[id*="gtin"]', '[id*="barcode"]',
    ]

    # Palavras-chave para contexto
    CONTEXT_KEYWORDS = ['upc', 'gtin', 'barcode', 'ean', 'item number', 'product code', 'sku']

    def __init__(self):
        self.methods_tried = []
        self.upc_found = None
        self.method_used = None

    def normalize_upc(self, value: str) -> Optional[str]:
        """Normaliza um valor para UPC válido (8, 12, 13 ou 14 dígitos)"""
        if not value:
            return None

        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', str(value))

        # Verifica se tem tamanho válido
        if len(digits) in (8, 12, 13, 14):
            # Valida que não é um número obviamente inválido
            if not digits.startswith('00000000') and digits not in ['000000000000', '111111111111', '999999999999']:
                return digits

        # Se for maior, tenta extrair 12-14 dígitos
        if len(digits) > 14:
            match = re.search(r'(\d{12,14})', digits)
            if match:
                candidate = match.group(1)
                if not candidate.startswith('00000000') and candidate not in ['000000000000', '111111111111', '999999999999']:
                    return candidate

        return None

    def extract_from_json_ld(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 1: Extrai de JSON-LD (schema.org)"""
        self.methods_tried.append('json-ld')

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                text = script.string
                if not text:
                    continue

                data = json.loads(text)

                # Busca recursiva em objetos
                def search_obj(obj):
                    if isinstance(obj, dict):
                        # PRIORIDADE 1: Busca direta por UPC/GTIN (NÃO MPN!)
                        for key in ['gtin', 'gtin12', 'gtin13', 'gtin14', 'upc', 'ean', 'ean13', 'productID']:
                            if key in obj:
                                upc = self.normalize_upc(str(obj[key]))
                                if upc:
                                    return upc

                        # Se encontrar mpn, ignora completamente
                        if 'mpn' in obj:
                            pass  # Ignora MPN - não é UPC!

                        # Busca em offers
                        if 'offers' in obj:
                            if isinstance(obj['offers'], dict):
                                result = search_obj(obj['offers'])
                                if result:
                                    return result
                            elif isinstance(obj['offers'], list):
                                for offer in obj['offers']:
                                    result = search_obj(offer)
                                    if result:
                                        return result

                        # Busca recursiva em todos os valores
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

    def extract_from_meta_tags(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 2: Extrai de meta tags"""
        self.methods_tried.append('meta-tags')

        # Busca em meta tags com atributos conhecidos
        meta_attrs = ['itemprop', 'property', 'name']

        for attr in meta_attrs:
            metas = soup.find_all('meta', attrs={attr: True})
            for meta in metas:
                attr_value = meta.get(attr, '').lower()

                # IMPORTANTE: Ignora MPN (Manufacturer Part Number) - queremos apenas UPC
                if 'mpn' in attr_value or 'partnumber' in attr_value or 'part_number' in attr_value:
                    continue

                # Verifica se o atributo contém palavras-chave de UPC
                if any(kw in attr_value for kw in ['gtin', 'upc', 'barcode', 'ean', 'productid']):
                    content = meta.get('content', '')
                    upc = self.normalize_upc(content)
                    if upc:
                        return upc

        return None

    def extract_from_css_selectors(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 3: Busca por seletores CSS específicos"""
        self.methods_tried.append('css-selectors')

        for selector in self.CSS_SELECTORS:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    # Tenta pegar de diferentes atributos
                    for attr in ['content', 'value', 'data-upc', 'data-gtin', 'data-barcode']:
                        value = elem.get(attr)
                        if value:
                            upc = self.normalize_upc(value)
                            if upc:
                                return upc

                    # Tenta pegar do texto
                    text = elem.get_text(strip=True)
                    if text:
                        upc = self.normalize_upc(text)
                        if upc:
                            return upc
            except Exception:
                continue

        return None

    def extract_from_scripts(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 4: Busca em scripts JavaScript"""
        self.methods_tried.append('javascript')

        for script in soup.find_all('script'):
            text = script.string or ''
            if not text:
                continue

            # Tenta vários padrões
            for pattern_name, pattern in self.PATTERNS.items():
                if pattern_name.startswith('json_') or pattern_name.startswith('js_') or pattern_name == 'shopify':
                    matches = pattern.findall(text)
                    for match in matches:
                        upc = self.normalize_upc(match)
                        if upc:
                            return upc

        return None

    def extract_from_window_objects(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 5: Busca em objetos window (Next.js, Shopify, etc)"""
        self.methods_tried.append('window-objects')

        for script in soup.find_all('script'):
            text = script.string or ''
            if not text:
                continue

            # Busca por objetos window comuns
            patterns = [
                r'window\.__NEXT_DATA__\s*=\s*({.+?});',
                r'window\.Shopify\s*=\s*({.+?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.dataLayer\s*=\s*(\[.+?\]);',
                r'window\.__APOLLO_STATE__\s*=\s*({.+?});',
                r'var\s+productData\s*=\s*({.+?});',
                r'const\s+product\s*=\s*({.+?});',
            ]

            for pattern in patterns:
                try:
                    match = re.search(pattern, text, re.I | re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        data = json.loads(json_str)

                        # Busca recursiva
                        def search_nested(obj, depth=0):
                            if depth > 10:  # Evita recursão infinita
                                return None

                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if isinstance(key, str) and any(kw in key.lower() for kw in ['gtin', 'upc', 'barcode', 'ean']):
                                        upc = self.normalize_upc(str(value))
                                        if upc:
                                            return upc

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

    def extract_from_labeled_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 6: Busca por texto com rótulos (UPC: 123456789012)"""
        self.methods_tried.append('labeled-text')

        text = soup.get_text(' ', strip=True)

        # Padrões para texto rotulado (UPC/GTIN APENAS, NÃO MPN!)
        patterns = [
            r'UPC\s*[:|\-]?\s*(\d{12,14})',
            r'GTIN-?1[2-4]\s*[:|\-]?\s*(\d{12,14})',
            r'Barcode\s*[:|\-]?\s*(\d{12,14})',
            r'EAN\s*[:|\-]?\s*(\d{13})',
            r'Item\s*#?\s*[:|\-]?\s*(\d{12,14})',
            r'Product\s*Code\s*[:|\-]?\s*(\d{12,14})',
            # REMOVIDO: Model # - pode confundir com MPN
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                # Verifica se não está perto de "MPN" no contexto
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].lower()

                # Se "mpn" aparece perto, ignora
                if 'mpn' in context or 'part number' in context:
                    continue

                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

        return None

    def extract_from_tables(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 7: Busca em tabelas de especificações (linhas e colunas)"""
        self.methods_tried.append('tables')

        for table in soup.find_all('table'):
            # MÉTODO 1: Tabela com linhas (label na primeira célula, valor na segunda)
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if any(kw in label for kw in self.CONTEXT_KEYWORDS):
                        upc = self.normalize_upc(value)
                        if upc:
                            return upc

            # MÉTODO 2: Tabela com COLUNAS (cabeçalho "UPC" na primeira linha, valores abaixo)
            # Exemplo: | Option | UPC | MPN |
            #          | Black  | 012527018741 | 601062 |
            if rows:
                # Pega primeira linha (cabeçalho)
                header_row = rows[0]
                headers = header_row.find_all(['th', 'td'])

                # Procura índice da coluna "UPC"
                upc_col_index = None
                for idx, header in enumerate(headers):
                    header_text = header.get_text(strip=True).lower()
                    if any(kw in header_text for kw in self.CONTEXT_KEYWORDS):
                        upc_col_index = idx
                        break

                # Se encontrou coluna UPC, pega valor da segunda linha em diante
                if upc_col_index is not None:
                    for row in rows[1:]:  # Pula cabeçalho
                        cells = row.find_all(['td', 'th'])
                        if len(cells) > upc_col_index:
                            value = cells[upc_col_index].get_text(strip=True)
                            upc = self.normalize_upc(value)
                            if upc:
                                return upc

        return None

    def extract_from_definition_lists(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 8: Busca em listas de definição (dl/dt/dd)"""
        self.methods_tried.append('definition-lists')

        for dl in soup.find_all('dl'):
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')

            for dt, dd in zip(dts, dds):
                label = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)

                if any(kw in label for kw in self.CONTEXT_KEYWORDS):
                    upc = self.normalize_upc(value)
                    if upc:
                        return upc

        return None

    def extract_from_product_details(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 9: Busca em divs de detalhes do produto"""
        self.methods_tried.append('product-details')

        # Seletores comuns para áreas de detalhes do produto
        detail_selectors = [
            '.product-details', '.product-info', '.product-specifications',
            '.product-meta', '.product-data', '#product-details',
            '.specs', '.specifications', '.attributes', '.product-attributes'
        ]

        for selector in detail_selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(' ', strip=True)

                    # Busca por padrões no texto
                    match = self.PATTERNS['labeled_text'].search(text)
                    if match:
                        upc = self.normalize_upc(match.group(1))
                        if upc:
                            return upc
            except Exception:
                continue

        return None

    def extract_from_structured_data_attributes(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 10: Busca em atributos data-* estruturados"""
        self.methods_tried.append('data-attributes')

        # Busca todos os elementos com atributos data-*
        all_elements = soup.find_all(attrs=lambda x: x and any(
            attr.startswith('data-') for attr in x.keys()
        ))

        for elem in all_elements:
            for attr, value in elem.attrs.items():
                if attr.startswith('data-'):
                    attr_lower = attr.lower()

                    # Verifica se o atributo contém palavras-chave
                    if any(kw in attr_lower for kw in ['upc', 'gtin', 'barcode', 'ean', 'sku']):
                        upc = self.normalize_upc(value if isinstance(value, str) else '')
                        if upc:
                            return upc

                    # Tenta parsear JSON em atributos data-*
                    if isinstance(value, str) and value.startswith('{'):
                        try:
                            data = json.loads(value)
                            for key in ['gtin', 'gtin12', 'gtin13', 'upc', 'barcode', 'ean']:
                                if key in data:
                                    upc = self.normalize_upc(str(data[key]))
                                    if upc:
                                        return upc
                        except (json.JSONDecodeError, Exception):
                            continue

        return None

    def extract_from_comments(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 11: Busca em comentários HTML"""
        self.methods_tried.append('html-comments')

        from bs4 import Comment
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        for comment in comments:
            text = str(comment)

            # Busca padrões em comentários
            for pattern in [self.PATTERNS['json_key'], self.PATTERNS['labeled_text']]:
                match = pattern.search(text)
                if match:
                    upc = self.normalize_upc(match.group(1))
                    if upc:
                        return upc

        return None

    def extract_from_image_alt_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 12: Busca em texto alternativo de imagens"""
        self.methods_tried.append('image-alt')

        for img in soup.find_all('img', alt=True):
            alt_text = img.get('alt', '')

            # Busca por padrões no alt text
            match = self.PATTERNS['labeled_text'].search(alt_text)
            if match:
                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

        return None

    def extract_from_api_json_pattern(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 13: Busca por padrões de API/JSON em qualquer script"""
        self.methods_tried.append('api-json-pattern')

        for script in soup.find_all('script'):
            text = script.string or ''
            if not text:
                continue

            # Busca por qualquer JSON que contenha campos de produto
            json_patterns = [
                r'"product"\s*:\s*({.+?})',
                r'"item"\s*:\s*({.+?})',
                r'"variant"\s*:\s*({.+?})',
                r'"sku"\s*:\s*"(\d{8,14})"',
            ]

            for pattern in json_patterns:
                try:
                    matches = re.finditer(pattern, text, re.I | re.DOTALL)
                    for match in matches:
                        json_str = match.group(1) if '{' in match.group(1) else '{"sku":"' + match.group(1) + '"}'

                        try:
                            data = json.loads(json_str)

                            for key in ['gtin', 'gtin12', 'gtin13', 'gtin14', 'upc', 'barcode', 'ean', 'sku']:
                                if key in data:
                                    upc = self.normalize_upc(str(data[key]))
                                    if upc:
                                        return upc
                        except (json.JSONDecodeError, Exception):
                            continue
                except Exception:
                    continue

        return None

    def extract_with_context_heuristic(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 14: Heurística - números de 12 dígitos próximos a palavras-chave"""
        self.methods_tried.append('context-heuristic')

        text = soup.get_text(' ', strip=True)

        # Encontra todos os números de 12 dígitos
        for match in self.PATTERNS['numeric_12'].finditer(text):
            number = match.group(1)

            # Pega contexto ao redor (100 caracteres antes e depois)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].lower()

            # Verifica se há palavras-chave no contexto
            if any(kw in context for kw in self.CONTEXT_KEYWORDS):
                upc = self.normalize_upc(number)
                if upc:
                    return upc

        return None

    def extract_from_forms(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 15: Busca em campos de formulário"""
        self.methods_tried.append('form-inputs')

        for form in soup.find_all('form'):
            inputs = form.find_all(['input', 'textarea', 'select'])

            for inp in inputs:
                # Verifica nome/id do campo
                name = (inp.get('name', '') + ' ' + inp.get('id', '')).lower()

                if any(kw in name for kw in self.CONTEXT_KEYWORDS):
                    value = inp.get('value', '')
                    upc = self.normalize_upc(value)
                    if upc:
                        return upc

        return None

    def extract_from_iframes(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 16: Busca em src de iframes"""
        self.methods_tried.append('iframes')

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if src:
                # Busca por UPC na URL do iframe
                match = re.search(r'(?:upc|gtin|barcode|ean)[=_](\d{12,14})', src, re.I)
                if match:
                    upc = self.normalize_upc(match.group(1))
                    if upc:
                        return upc

        return None

    def extract_from_image_urls(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 17: Busca em URLs de imagens (MUITO CAUTELOSO)"""
        self.methods_tried.append('image-urls')

        # Coleta todos os números de imagens primeiro
        all_numbers = []
        for img in soup.find_all('img'):
            src = img.get('src', '') + ' ' + img.get('data-src', '')

            # Busca APENAS no nome do arquivo (não no path/domínio)
            # Pega só a última parte da URL
            if '/' in src:
                filename = src.split('/')[-1]
            else:
                filename = src

            # Busca por UPC no nome do arquivo
            matches = re.findall(r'(\d{12,14})', filename)
            for match in matches:
                upc = self.normalize_upc(match)
                if upc:
                    all_numbers.append(upc)

        # Se o mesmo número aparece em TODAS as imagens, provavelmente NÃO é UPC
        # (pode ser ID de sessão, versão do site, etc)
        if not all_numbers:
            return None

        # Conta frequência de cada número
        from collections import Counter
        counter = Counter(all_numbers)

        # Se um número aparece MUITO (>50% das imagens), descarta ele
        total_images = len(all_numbers)
        for number, count in counter.most_common():
            # Se aparece em menos de 50% das imagens, provavelmente é o UPC do produto
            if count / total_images < 0.5:
                return number

        return None

    def extract_from_class_and_id_names(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 18: Busca em nomes de classes e IDs (alguns sites colocam o UPC aqui)"""
        self.methods_tried.append('class-id-names')

        all_elements = soup.find_all(True)  # Todos os elementos
        for elem in all_elements:
            # Verifica classes
            classes = elem.get('class', [])
            if isinstance(classes, list):
                for cls in classes:
                    if isinstance(cls, str):
                        match = re.search(r'(\d{12,14})', cls)
                        if match:
                            upc = self.normalize_upc(match.group(1))
                            if upc:
                                return upc

            # Verifica ID
            elem_id = elem.get('id', '')
            if elem_id:
                match = re.search(r'(\d{12,14})', elem_id)
                if match:
                    upc = self.normalize_upc(match.group(1))
                    if upc:
                        return upc

        return None

    def extract_from_breadcrumbs(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 19: Busca em breadcrumbs"""
        self.methods_tried.append('breadcrumbs')

        # Seletores comuns para breadcrumbs
        breadcrumb_selectors = [
            '.breadcrumb', '.breadcrumbs', '[itemtype*="BreadcrumbList"]',
            '#breadcrumb', '#breadcrumbs', '.navigation-path'
        ]

        for selector in breadcrumb_selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(' ', strip=True)
                    match = re.search(r'(\d{12,14})', text)
                    if match:
                        upc = self.normalize_upc(match.group(1))
                        if upc:
                            return upc
            except Exception:
                continue

        return None

    def extract_from_aria_labels(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 20: Busca em aria-labels e aria-describedby"""
        self.methods_tried.append('aria-labels')

        # Busca todos os elementos com aria-label ou aria-describedby
        for elem in soup.find_all(attrs={'aria-label': True}):
            aria_label = elem.get('aria-label', '')
            match = re.search(r'(\d{12,14})', aria_label)
            if match:
                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

        return None

    def extract_from_spans_and_divs_with_numbers(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 21: Busca em spans/divs que contêm apenas números longos"""
        self.methods_tried.append('numeric-spans-divs')

        for tag in soup.find_all(['span', 'div', 'p', 'td']):
            text = tag.get_text(strip=True)
            # Se o texto é basicamente só números (permite espaços/traços)
            cleaned = re.sub(r'[\s\-]', '', text)
            if cleaned.isdigit() and len(cleaned) in (12, 13, 14):
                upc = self.normalize_upc(cleaned)
                if upc:
                    # Verifica se está em um contexto de produto
                    parent_text = ''
                    if tag.parent:
                        parent_text = tag.parent.get_text(' ', strip=True).lower()

                    # Se tem palavras relacionadas ao UPC perto, é mais confiável
                    if any(kw in parent_text for kw in ['upc', 'gtin', 'barcode', 'ean', 'item', 'sku']):
                        return upc

        return None

    def extract_from_placeholder_values(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 22: Busca em placeholders de inputs"""
        self.methods_tried.append('placeholders')

        for inp in soup.find_all('input', placeholder=True):
            placeholder = inp.get('placeholder', '')
            match = re.search(r'(\d{12,14})', placeholder)
            if match:
                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

        return None

    def extract_from_title_attributes(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 23: Busca em atributos title"""
        self.methods_tried.append('title-attributes')

        for elem in soup.find_all(title=True):
            title = elem.get('title', '')
            # Busca por padrão rotulado
            match = re.search(r'(?:UPC|GTIN|Barcode|EAN)\s*[:|\-]?\s*(\d{12,14})', title, re.I)
            if match:
                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

            # Busca por números soltos no title
            match = re.search(r'(\d{12,14})', title)
            if match:
                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

        return None

    def extract_from_link_urls(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 24: Busca UPC em URLs de links (parâmetros e paths)"""
        self.methods_tried.append('link-urls')

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # Busca por padrão upc=123456789012 ou gtin=123456789012
            match = re.search(r'(?:upc|gtin|barcode|ean|item)[=_/](\d{12,14})', href, re.I)
            if match:
                upc = self.normalize_upc(match.group(1))
                if upc:
                    return upc

        return None

    def extract_from_raw_script_objects(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 25: Busca em declarações de objetos JavaScript (var/let/const product = ...)"""
        self.methods_tried.append('raw-script-objects')

        for script in soup.find_all('script'):
            text = script.string or ''
            if not text:
                continue

            # Busca por padrões de declaração de variáveis de produto
            patterns = [
                r'(?:var|let|const)\s+(?:product|item|productData|itemData)\s*=\s*({[^;]+})',
                r'product\s*:\s*({[^}]+})',
                r'"product"\s*:\s*({[^}]+})',
            ]

            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, text, re.I | re.DOTALL)
                    for match in matches:
                        json_str = match.group(1)

                        # Tenta parsear como JSON
                        try:
                            # Limpa o JSON (remove trailing commas, etc)
                            json_str = re.sub(r',\s*}', '}', json_str)
                            json_str = re.sub(r',\s*]', ']', json_str)

                            data = json.loads(json_str)

                            # Busca recursiva por UPC
                            def search_nested(obj, depth=0):
                                if depth > 8:
                                    return None

                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if isinstance(key, str):
                                            key_lower = key.lower()
                                            if any(kw in key_lower for kw in ['gtin', 'upc', 'barcode', 'ean']):
                                                upc = self.normalize_upc(str(value))
                                                if upc:
                                                    return upc

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
                            # Se não parsear como JSON, tenta regex direto no texto
                            upc_match = re.search(r'(?:gtin|upc|barcode|ean)["\']?\s*:\s*["\']?(\d{12,14})["\']?', json_str, re.I)
                            if upc_match:
                                upc = self.normalize_upc(upc_match.group(1))
                                if upc:
                                    return upc

                except Exception:
                    continue

        return None

    def extract_aggressive_numeric_scan(self, soup: BeautifulSoup) -> Optional[str]:
        """Método 26: SUPER AGRESSIVO - Busca TODOS os números de 12-14 dígitos na página"""
        self.methods_tried.append('aggressive-numeric-scan')

        text = soup.get_text(' ', strip=True)

        # Lista para armazenar candidatos com pontuação
        candidates = []

        # Busca por números de 12, 13 e 14 dígitos (permite traços e espaços)
        for length in [12, 13, 14]:
            # Padrão que permite espaços e traços entre os dígitos
            pattern = re.compile(rf'(\d[\s\-]?){{{length-1}}}\d')
            for match in pattern.finditer(text):
                number_raw = match.group(0)
                number = re.sub(r'[\s\-]', '', number_raw)  # Remove espaços e traços

                if not number.isdigit() or len(number) not in (12, 13, 14):
                    continue

                # Pega contexto ao redor (200 caracteres antes e depois)
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end].lower()

                # Pontuação baseada em palavras-chave no contexto
                score = 0

                # Palavras-chave fortes (pontuação alta)
                strong_keywords = ['upc', 'gtin', 'barcode', 'ean']
                for kw in strong_keywords:
                    if kw in context:
                        score += 10

                # Palavras-chave médias
                medium_keywords = ['item number', 'product code', 'sku', 'model', 'item #', 'code']
                for kw in medium_keywords:
                    if kw in context:
                        score += 5

                # Palavras-chave fracas (indicam que é produto)
                weak_keywords = ['product', 'item', 'details', 'specifications', 'info']
                for kw in weak_keywords:
                    if kw in context:
                        score += 1

                # Penaliza se tiver palavras que indicam que não é UPC
                bad_keywords = ['phone', 'zip', 'postal', 'credit card', 'date', 'time', 'year', 'price', 'order', 'tracking']
                for kw in bad_keywords:
                    if kw in context:
                        score -= 5

                # Valida: não pode começar com 000, 999 ou ter muitos zeros
                if number.startswith('000') or number.startswith('999'):
                    score -= 3

                # Penaliza números que são muito repetitivos (111111111111, 123456789012, etc)
                if len(set(number)) < 4:  # Menos de 4 dígitos diferentes
                    score -= 5

                if score > 0:
                    candidates.append((number, score))

        # Ordena por pontuação (maior primeiro)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Retorna o candidato com maior pontuação
        if candidates:
            return self.normalize_upc(candidates[0][0])

        return None

    def extract_all_methods(self, html: str) -> Optional[str]:
        """
        Executa TODOS os métodos de extração em ordem de prioridade
        Retorna o primeiro UPC válido encontrado
        """
        self.methods_tried = []
        self.upc_found = None
        self.method_used = None

        soup = BeautifulSoup(html, 'html.parser')

        # Ordem de prioridade dos métodos (26 métodos!)
        # MÉTODOS MAIS CONFIÁVEIS PRIMEIRO, MENOS CONFIÁVEIS NO FINAL
        extraction_methods = [
            # Alta confiabilidade - dados estruturados
            self.extract_from_json_ld,                      # 1. JSON-LD Schema.org
            self.extract_from_meta_tags,                    # 2. Meta tags
            self.extract_from_css_selectors,                # 3. Seletores CSS específicos
            self.extract_from_structured_data_attributes,   # 4. Atributos data-*
            self.extract_from_window_objects,               # 5. Window.__NEXT_DATA__, etc

            # Média confiabilidade - JavaScript e APIs
            self.extract_from_scripts,                      # 6. Scripts JavaScript
            self.extract_from_api_json_pattern,             # 7. Padrões de API
            self.extract_from_raw_script_objects,           # 8. Objetos JavaScript diretos
            self.extract_from_forms,                        # 9. Campos de formulário

            # Média-baixa confiabilidade - conteúdo estruturado
            self.extract_from_product_details,              # 10. Divs de detalhes
            self.extract_from_labeled_text,                 # 11. Texto rotulado (UPC: xxx)
            self.extract_from_tables,                       # 12. Tabelas
            self.extract_from_definition_lists,             # 13. Listas de definição
            self.extract_from_comments,                     # 14. Comentários HTML

            # Baixa confiabilidade - atributos e contexto
            self.extract_from_aria_labels,                  # 15. Aria labels
            self.extract_from_placeholder_values,           # 16. Placeholders
            self.extract_from_title_attributes,             # 17. Atributos title
            self.extract_from_image_alt_text,               # 18. Alt text de imagens
            self.extract_with_context_heuristic,            # 19. Heurística de contexto

            # MUITO BAIXA confiabilidade - só use como último recurso!
            self.extract_from_spans_and_divs_with_numbers,  # 20. Spans/divs com números
            self.extract_from_link_urls,                    # 21. URLs de links
            self.extract_from_iframes,                      # 22. URLs de iframes
            self.extract_from_breadcrumbs,                  # 23. Breadcrumbs
            self.extract_from_class_and_id_names,           # 24. Classes e IDs
            self.extract_from_image_urls,                   # 25. URLs de imagens (CAUTELOSO!)
            self.extract_aggressive_numeric_scan,           # 26. Último recurso - super agressivo!
        ]

        for method in extraction_methods:
            try:
                result = method(soup)
                if result:
                    self.upc_found = result
                    self.method_used = self.methods_tried[-1] if self.methods_tried else 'unknown'
                    return result
            except Exception as e:
                # Log silencioso, continua tentando outros métodos
                continue

        return None

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre a extração"""
        return {
            'upc_found': self.upc_found,
            'method_used': self.method_used,
            'methods_tried': len(self.methods_tried),
            'all_methods': self.methods_tried
        }


# Função auxiliar para compatibilidade com código existente
def extract_upc_from_html(html: str) -> Optional[str]:
    """
    Função auxiliar que usa o UPCExtractor
    Mantém compatibilidade com código existente
    """
    extractor = UPCExtractor()
    return extractor.extract_all_methods(html)
