from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import Response

from app.core.redis import get_redis


IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
DEFAULT_TTL_SECONDS = 60 * 60 * 24  # 24 hours


@dataclass(frozen=True)
class CachedResponse:
    status_code: int
    headers: dict[str, str]
    body_b64: str

    @classmethod
    def from_response(cls, response: Response, body: bytes) -> "CachedResponse":
        headers = _filtered_headers(response.headers)
        return cls(
            status_code=response.status_code,
            headers=headers,
            body_b64=base64.b64encode(body).decode("ascii"),
        )

    def to_response(self) -> Response:
        body = base64.b64decode(self.body_b64.encode("ascii"))
        return Response(content=body, status_code=self.status_code, headers=self.headers)


def _filtered_headers(headers: Headers) -> dict[str, str]:
    hop_by_hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
    out: dict[str, str] = {}
    for key, value in headers.items():
        lower = key.lower()
        if lower in hop_by_hop:
            continue
        if lower == "content-length":
            continue
        out[key] = value
    return out


def _request_fingerprint(request: Request, body: bytes) -> str:
    # Incorporate method, path, query, and auth header to reduce collisions.
    auth = request.headers.get("authorization", "")
    base = f"{request.method}:{request.url.path}:{request.url.query}:{auth}".encode()
    digest = hashlib.sha256(base + body).hexdigest()
    return digest


def _cache_key(request: Request, *, body: bytes) -> str:
    header_value = request.headers.get(IDEMPOTENCY_HEADER, "").strip()
    fingerprint = _request_fingerprint(request, body)
    return f"idempotency:{header_value}:{fingerprint}"


def load_cached_response(request: Request, *, body: bytes) -> Response | None:
    header_value = request.headers.get(IDEMPOTENCY_HEADER)
    if not header_value:
        return None
    key = _cache_key(request, body=body)
    raw = get_redis().get(key)
    if not raw:
        return None
    payload = json.loads(raw)
    cached = CachedResponse(**payload)
    return cached.to_response()


def store_cached_response(
    request: Request,
    *,
    body: bytes,
    response: Response,
    response_body: bytes,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> None:
    header_value = request.headers.get(IDEMPOTENCY_HEADER)
    if not header_value:
        return
    key = _cache_key(request, body=body)
    cached = CachedResponse.from_response(response, response_body)
    get_redis().setex(key, ttl_seconds, json.dumps(asdict(cached)))
