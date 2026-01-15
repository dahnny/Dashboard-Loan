from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any, Callable, TypeVar

import anyio
from supabase import Client, create_client

from app.core.config import settings


def _require_storage_config() -> tuple[str, str]:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL not configured")
    if not settings.supabase_anon_key:
        raise RuntimeError("SUPABASE_ANON_KEY not configured")
    print( settings.supabase_url, settings.supabase_anon_key)
    return settings.supabase_url.strip(), settings.supabase_anon_key.strip()    


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


T = TypeVar("T")


async def _run_in_thread(func: Callable[[], T]) -> T:
    return await anyio.to_thread.run_sync(func)


@lru_cache(maxsize=1)
def _get_supabase_client() -> Client:
    base, anon_key = _require_storage_config()
    return create_client(base, anon_key)


def _normalize_object_path(object_path: str) -> str:
    return object_path.lstrip("/")


async def upload_object(*, bucket: str, object_path: str, content: bytes, content_type: str | None) -> None:
    client = _get_supabase_client()
    storage = client.storage.from_(bucket)
    path = _normalize_object_path(object_path)
    options: dict[str, Any] = {"upsert": "true"}
    if content_type:
        options["content-type"] = content_type 

    def _upload() -> Any:
        return storage.upload(path, content, file_options=options)

    result = await _run_in_thread(_upload)
    if isinstance(result, dict):
        error = result.get("error")
        if error:
            raise RuntimeError(f"Supabase upload failed: {error}")


async def create_signed_url(*, bucket: str, object_path: str, expires_in: int = 60) -> str:
    client = _get_supabase_client()
    storage = client.storage.from_(bucket)
    path = _normalize_object_path(object_path)

    def _sign() -> Any:
        return storage.create_signed_url(path, expires_in)

    data = await _run_in_thread(_sign)

    signed = None
    if isinstance(data, dict):
        signed = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
    elif isinstance(data, str):
        signed = data

    if not signed:
        raise RuntimeError("Supabase did not return signedURL")

    # Supabase returns a relative path; convert to absolute URL.
    if signed.startswith("http"):
        return signed
    base, _ = _require_storage_config()
    return f"{base}{signed}"
