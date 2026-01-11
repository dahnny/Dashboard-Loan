from __future__ import annotations

import hashlib

import httpx

from app.core.config import settings


def _require_storage_config() -> tuple[str, str]:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL not configured")
    if not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY not configured")
    return settings.supabase_url.rstrip("/"), settings.supabase_service_role_key


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def upload_object(*, bucket: str, object_path: str, content: bytes, content_type: str | None) -> None:
    base, service_key = _require_storage_config()
    url = f"{base}/storage/v1/object/{bucket}/{object_path.lstrip('/')}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "x-upsert": "true",
    }
    if content_type:
        headers["Content-Type"] = content_type

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, content=content)
        resp.raise_for_status()


async def create_signed_url(*, bucket: str, object_path: str, expires_in: int = 60) -> str:
    base, service_key = _require_storage_config()
    url = f"{base}/storage/v1/object/sign/{bucket}/{object_path.lstrip('/')}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=headers, json={"expiresIn": expires_in})
        resp.raise_for_status()
        data = resp.json()

    signed = data.get("signedURL") or data.get("signedUrl")
    if not signed:
        raise RuntimeError("Supabase did not return signedURL")

    # Supabase returns a relative path; convert to absolute URL.
    if signed.startswith("http"):
        return signed
    return f"{base}{signed}"
