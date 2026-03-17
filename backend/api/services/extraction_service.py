from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

from playwright.async_api import Page

from ..title_extractor import TitleExtractor
from ..upc_extractor import UPCExtractor

UPC_INLINE_RE = re.compile(
    r"(?:\bUPC\b|\bGTIN-?1[2-4]\b|\bGTIN\b|\bBarcode\b|\buniversal product code\b)\D*?(\d{8}|\d{12,14})",
    re.I,
)
DIGITS_RE = re.compile(r"\D+")
KEY_HINTS = ("api", "ajax", "json", "product", "item", "variant", "catalog", "v1", "v2", "graphql")


def only_digits(value: str) -> str:
    return DIGITS_RE.sub("", value or "")


def normalize_upc(value: str) -> Optional[str]:
    digits = only_digits(value)
    if len(digits) in (8, 12, 13, 14):
        return digits

    match = re.search(r"(\d{12,14})", digits)
    return match.group(1) if match else None


def cache_key(url: str) -> str:
    parsed = urlparse(url)
    key = f"{parsed.netloc}{parsed.path}"
    if parsed.query:
        key += f"?{parsed.query}"
    return key.rstrip("/").lower() or url.lower()


def base_domain(host: str) -> str:
    parts = (host or "").split(".")
    if len(parts) >= 3:
        return ".".join(parts[-2:]).lower()
    return (host or "").lower()


def same_site(host: str, reference_host: str) -> bool:
    return base_domain(host) == base_domain(reference_host)


def normalize_text(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.strip().lower())


def pick_title(candidates: List[str]) -> str:
    for candidate in candidates:
        candidate = (candidate or "").strip()
        if candidate:
            return candidate
    return "Sem título"


def find_upc_in_obj(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        for key, inner_value in value.items():
            lower = str(key).lower()
            if any(token in lower for token in ("gtin", "gtin12", "gtin13", "gtin14", "upc", "barcode")):
                normalized = normalize_upc(str(inner_value))
                if normalized:
                    return normalized

        for common_key in (
            "offers",
            "product",
            "item",
            "data",
            "props",
            "pageProps",
            "productInfo",
            "details",
            "attributes",
            "variants",
            "items",
        ):
            if common_key in value:
                nested = find_upc_in_obj(value[common_key])
                if nested:
                    return nested

        for inner_value in value.values():
            nested = find_upc_in_obj(inner_value)
            if nested:
                return nested

    elif isinstance(value, list):
        for item in value:
            nested = find_upc_in_obj(item)
            if nested:
                return nested

    return None


async def robust_page_title(page: Page, timeout_ms: int = 1600) -> str:
    try:
        title = await asyncio.wait_for(page.title(), timeout=timeout_ms / 1000)
        if title and title.strip():
            return title.strip()
    except Exception:
        pass

    try:
        title = await page.evaluate("document.title || ''", timeout=timeout_ms)
        if title and title.strip():
            return title.strip()
    except Exception:
        pass

    try:
        js = """
(() => {
  const pick = (selector) => {
    const element = document.querySelector(selector);
    return element ? (element.content || element.textContent || '').trim() : '';
  };
  return pick('meta[property="og:title"]') || pick('meta[name="twitter:title"]') || '';
})()
"""
        title = await page.evaluate(js, timeout=timeout_ms)
        if title and title.strip():
            return title.strip()
    except Exception:
        pass

    return ""


async def read_quick(page: Page, timeout_ms: int = 1800) -> Dict[str, Any]:
    js = """
(() => {
  const out = {};
  const pick = (selector) => {
    const element = document.querySelector(selector);
    return element ? (element.content || element.textContent || '').trim() : '';
  };

  out.meta_og = pick('meta[property="og:title"]');
  out.meta_tw = pick('meta[name="twitter:title"]');
  out.h1 = (() => {
    const element = document.querySelector('h1.pdp-title, h1.product_title, h1[itemprop="name"], h1.entry-title, h1');
    return element ? element.textContent.trim() : '';
  })();
  out.itemprop_name = pick('[itemprop="name"]');

  out.jsonld = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach((script) => {
    if (script.textContent) out.jsonld.push(script.textContent.trim());
  });

  out.meta_gtin = [];
  document.querySelectorAll('meta[itemprop], meta[name], meta[property]').forEach((meta) => {
    const name = (meta.getAttribute('itemprop') || meta.getAttribute('name') || meta.getAttribute('property') || '').toLowerCase();
    if (name.includes('gtin') || name.includes('upc') || name.includes('barcode')) {
      out.meta_gtin.push({ name, content: (meta.getAttribute('content') || '').trim() });
    }
  });

  out.scripts = [];
  document.querySelectorAll('script').forEach((script) => {
    const text = (script.textContent || '').trim();
    if (text) out.scripts.push(text.slice(0, 250000));
  });

  const main = document.querySelector('main') || document.body;
  out.text = (main.innerText || '').slice(0, 180000);

  out.script_urls = [];
  const urlRegex = /["'](https?:\\/\\/[^"']+?|\\/.+?)(?=["'])/ig;
  for (const script of document.querySelectorAll('script')) {
    const text = script.textContent || '';
    if (!text) continue;
    const matches = text.matchAll(urlRegex);
    for (const match of matches) out.script_urls.push(match[1]);
  }

  out.res_urls = [];
  try {
    const perf = performance.getEntriesByType('resource') || [];
    for (const entry of perf) {
      if (entry.name && typeof entry.name === 'string') out.res_urls.push(entry.name);
    }
  } catch (_) {}

  out.link_urls = [];
  document.querySelectorAll('[href],[src]').forEach((element) => {
    const url = element.getAttribute('href') || element.getAttribute('src');
    if (url) out.link_urls.push(url);
  });

  out.window_blobs = {};
  try {
    const keys = [
      '__NEXT_DATA__', '__APOLLO_STATE__', '__NUXT__',
      'Shopify', 'ShopifyAnalytics', 'dataLayer',
      '__INITIAL_STATE__', 'INITIAL_STATE', 'drupalSettings'
    ];

    keys.forEach((key) => {
      if (window[key]) {
        try {
          out.window_blobs[key] = JSON.stringify(window[key]).slice(0, 300000);
        } catch (_) {}
      }
    });
  } catch (_) {}

  return out;
})()
"""

    try:
        data = await page.evaluate(js, timeout=timeout_ms)
    except Exception:
        data = {
            "jsonld": [],
            "meta_gtin": [],
            "scripts": [],
            "text": "",
            "script_urls": [],
            "res_urls": [],
            "link_urls": [],
            "window_blobs": {},
        }

    try:
        data["doc_title"] = await robust_page_title(page, timeout_ms)
    except Exception:
        data.setdefault("doc_title", "")

    return data


def extract_title(quick_data: Dict[str, Any]) -> str:
    return pick_title(
        [
            quick_data.get("meta_og"),
            quick_data.get("meta_tw"),
            quick_data.get("h1"),
            quick_data.get("itemprop_name"),
            quick_data.get("doc_title"),
        ]
    )


def try_json_payloads(payloads: List[str]) -> Optional[str]:
    for raw in payloads or []:
        try:
            parsed = json.loads(raw)
        except Exception:
            match = re.findall(
                r'["\'](gtin(?:12|13|14)?|upc|barcode)["\']\s*:\s*["\']?(\d{8}|\d{12,14})["\']?',
                raw,
                flags=re.I,
            )
            if match:
                return normalize_upc(match[0][1])
            continue

        found = find_upc_in_obj(parsed)
        if found:
            return found

    return None


def extract_upc_local(quick_data: Dict[str, Any]) -> Tuple[Optional[str], str]:
    upc = try_json_payloads(quick_data.get("jsonld"))
    if upc:
        return upc, "json-ld"

    for meta in quick_data.get("meta_gtin", []):
        upc = normalize_upc(meta.get("content", ""))
        if upc:
            return upc, "meta"

    if isinstance(quick_data.get("window_blobs"), dict) and quick_data["window_blobs"]:
        upc = try_json_payloads(list(quick_data["window_blobs"].values()))
        if upc:
            return upc, "window"

    upc = try_json_payloads(quick_data.get("scripts"))
    if upc:
        return upc, "script"

    match = UPC_INLINE_RE.search(quick_data.get("text") or "")
    if match:
        normalized = normalize_upc(match.group(1))
        if normalized:
            return normalized, "text"

    return None, ""


def looks_jsonish(url: str) -> bool:
    lowered = url.lower()
    if ".json" in lowered:
        return True
    if "/api/" in lowered or "/ajax/" in lowered:
        return True
    if any(hint in lowered for hint in KEY_HINTS):
        return True

    try:
        query = parse_qs(urlparse(url).query)
        if "json" in query or query.get("format", [""])[0] == "json":
            return True
    except Exception:
        pass

    return False


def same_domain_candidates(product_url: str, quick_data: Dict[str, Any], aggressive: bool = False) -> List[str]:
    parsed = urlparse(product_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    raw_urls = set()
    for values in (quick_data.get("script_urls", []), quick_data.get("res_urls", []), quick_data.get("link_urls", [])):
        for value in values:
            if value:
                raw_urls.add(value.strip())

    candidates: List[str] = []
    for raw_url in raw_urls:
        try:
            candidate = raw_url.strip().strip('"\'')
            if candidate.startswith("//"):
                candidate = f"{parsed.scheme}:{candidate}"
            if candidate.startswith("/"):
                candidate = urljoin(origin, candidate)

            host = urlparse(candidate).netloc
            if host and same_site(host, parsed.netloc):
                if looks_jsonish(candidate) or aggressive:
                    candidates.append(candidate)
        except Exception:
            continue

    unique: List[str] = []
    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)

    return unique


async def fetch_json_inside_page(page: Page, url: str, timeout_ms: int) -> Optional[str]:
    js = """
async ({url, timeoutMs}) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      credentials: 'include',
      headers: { accept: 'application/json,text/*' },
      signal: controller.signal,
    });
    const text = await response.text();
    return text.slice(0, 500000);
  } catch (_) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}
"""

    try:
        return await page.evaluate(js, {"url": url, "timeoutMs": timeout_ms})
    except Exception:
        return None


async def detect_product_apis(page: Page, timeout_ms: int = 2000) -> List[str]:
    js = """
async ({timeoutMs}) => {
  const apis = [];
  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.initiatorType === 'xmlhttprequest' || entry.initiatorType === 'fetch') {
          const lowered = (entry.name || '').toLowerCase();
          if (
            lowered.includes('product') ||
            lowered.includes('item') ||
            lowered.includes('api') ||
            lowered.includes('catalog') ||
            lowered.includes('detail') ||
            lowered.includes('info') ||
            lowered.includes('.json') ||
            lowered.includes('/ajax/')
          ) {
            apis.push(entry.name);
          }
        }
      }
    });

    observer.observe({ entryTypes: ['resource'] });
    await new Promise((resolve) => setTimeout(resolve, timeoutMs));
    observer.disconnect();
  } catch (_) {}

  return [...new Set(apis)];
}
"""

    try:
        return await page.evaluate(js, {"timeoutMs": timeout_ms})
    except Exception:
        return []


async def same_domain_probe(
    product_url: str,
    page: Page,
    quick_data: Dict[str, Any],
    timeout_ms: int = 3500,
    max_urls: int = 12,
    aggressive: bool = False,
) -> Optional[Tuple[str, str]]:
    detected_apis = await detect_product_apis(page, 1500)
    candidates = same_domain_candidates(product_url, quick_data, aggressive)
    all_candidates = detected_apis + [candidate for candidate in candidates if candidate not in detected_apis]

    if not all_candidates:
        return None

    for index, candidate_url in enumerate(all_candidates):
        if index >= max_urls:
            break

        payload = await fetch_json_inside_page(page, candidate_url, timeout_ms)
        if not payload:
            continue

        try:
            parsed = json.loads(payload)
            upc = find_upc_in_obj(parsed)
            if upc:
                return upc, f"same-domain:{candidate_url}"
        except Exception:
            pass

        match = re.search(
            r'(gtin(?:12|13|14)?|upc|barcode|universal product code)["\']?\s*[:=]\s*["\']?(\d{8}|\d{12,14})',
            payload,
            flags=re.I,
        )
        if match:
            upc = normalize_upc(match.group(2))
            if upc:
                return upc, f"same-domain:{candidate_url}"

    return None


async def extract_page_fast(page: Page, timeout_ms: int = 1800) -> Dict[str, Any]:
    quick_data = await read_quick(page, timeout_ms)
    title = extract_title(quick_data)
    upc, source = extract_upc_local(quick_data)
    html = None

    if not upc:
        try:
            html = await page.content()
            if html:
                extractor = UPCExtractor()
                advanced = extractor.extract_all_methods(html)
                if advanced:
                    upc = advanced
                    source = f"advanced:{extractor.method_used}" if extractor.method_used else "advanced"
        except Exception:
            pass

    if not title or title == "Sem título":
        try:
            if html is None:
                html = await page.content()
            if html:
                title_extractor = TitleExtractor()
                advanced_title = title_extractor.extract_all_methods(html)
                if advanced_title and advanced_title != "Sem título":
                    title = advanced_title
        except Exception:
            pass

    return {
        "_raw": quick_data,
        "product_title": title or "Sem título",
        "upc": upc or "",
        "upc_method": source or "",
    }
