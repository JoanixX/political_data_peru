import hashlib
import functools
from typing import Any, Callable
from cachetools import TTLCache
from fastapi import Request, Response
from backend.src.config.settings import settings

# cache compartido entre todos los endpoints
_response_cache: TTLCache = TTLCache(
    maxsize=settings.cache_max_size,
    ttl=settings.cache_ttl_seconds,
)

# hash que se actualiza cuando el repo recarga datos
_current_etag: str = ""

def set_current_etag(etag: str) -> None:
    global _current_etag
    if _current_etag != etag:
        _response_cache.clear()
    _current_etag = etag

def get_current_etag() -> str:
    return _current_etag

def build_cache_key(request: Request) -> str:
    return f"{request.url.path}?{request.url.query or ''}"

def check_etag_match(request: Request) -> bool:
    client_etag = request.headers.get("if-none-match", "")
    # por si el header va con comillas
    clean = client_etag.strip('"').strip()
    return clean == _current_etag and _current_etag != ""

def apply_cache_headers(response: Response) -> None:
    if _current_etag:
        response.headers["ETag"] = f'"{_current_etag}"'
    response.headers["Cache-Control"] = f"public, max-age={settings.cache_ttl_seconds}"

def get_cached(key: str) -> Any | None:
    return _response_cache.get(key)

def set_cached(key: str, value: Any) -> None:
    _response_cache[key] = value