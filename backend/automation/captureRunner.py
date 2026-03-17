import asyncio
import httpx
import os
import re


def _build_exact_urls_regex(urls):
    escaped = [re.escape(u) for u in urls if u]
    if not escaped:
        return ""
    return "^(?:" + "|".join(escaped) + ")$"


async def call_capture_api(devtools_url, target_urls, fast_mode=True, max_retries=4):
    """
    Chama a API local /api/capture/capture-tabs para rodar a extração de abas simultâneas.
    """
    url = "http://127.0.0.1:8001/api/capture/capture-tabs"

    include_pattern = ""
    if isinstance(target_urls, int):
        requested_limit = max(1, target_urls)
    else:
        urls = [u for u in (target_urls or []) if isinstance(u, str) and u.strip()]
        if not urls:
            return []
        requested_limit = len(urls)
        include_pattern = _build_exact_urls_regex(urls)

    max_concurrency = max(1, int(os.getenv("CAPTURE_MAX_CONCURRENCY", "7")))
    capture_concurrency = min(requested_limit, max_concurrency)
    per_page_timeout_ms = max(1200, int(os.getenv("CAPTURE_PER_PAGE_TIMEOUT_MS", "2200")))
    capture_api_timeout_seconds = max(40, int(os.getenv("CAPTURE_API_TIMEOUT_SECONDS", "120")))

    params = {
        "devtools_url": devtools_url,
        "concurrency": str(capture_concurrency),
        "fast": "1" if fast_mode else "0",
        "limit": str(requested_limit),
        "skip": "0",
        "per_page_timeout_ms": str(per_page_timeout_ms),
        "use_cache": "1"
    }
    if include_pattern:
        params["include_pattern"] = include_pattern

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=float(capture_api_timeout_seconds)) as client:
                resp = await client.post(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                tabs = data.get("tabs")
                if isinstance(tabs, list):
                    return tabs
                raise RuntimeError("Resposta da API de captura sem campo 'tabs' válido.")
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                await asyncio.sleep(min(12, attempt * 2))

    raise RuntimeError(f"Falha chamando API de captura após {max_retries} tentativas: {last_error}")
