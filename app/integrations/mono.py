from __future__ import annotations

import httpx
import uuid
from app.core.config import settings


class MonoError(RuntimeError):
    pass


def _require_config() -> tuple[str, str]:
    if not settings.mono_base_url or not settings.mono_secret_key:
        raise MonoError("Mono config missing: set MONO_BASE_URL and MONO_SECRET_KEY")
    return settings.mono_base_url.rstrip("/"), settings.mono_secret_key


async def create_mandate_link(*, customer_email: str, customer_name: str) -> str:
    base, secret = _require_config()
    url = f"{base}/dd/mandates/link"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    payload = {
        "customer": {
            "email": customer_email,
            "name": customer_name,
        }
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise MonoError(resp.text)
    data = resp.json()
    link = data.get("link") or data.get("url")
    if not link:
        raise MonoError("Mono did not return a mandate link")
    return link


async def charge_mandate(*, mandate_reference: str, amount_minor: int, idempotency_key: str | None = None) -> dict:
    base, secret = _require_config()
    url = f"{base}/dd/mandates/{mandate_reference}/charge"
    headers = {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key or str(uuid.uuid4()),
    }
    payload = {"amount": amount_minor}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise MonoError(resp.text)
    return resp.json()
