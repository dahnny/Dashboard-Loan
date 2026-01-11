from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from jose import JWTError, jwt

from app.core.config import settings


@dataclass(frozen=True)
class SupabasePrincipal:
    sub: str
    email: str | None
    roles: set[str]
    raw_claims: dict


class SupabaseJWTVerifier:
    def __init__(self) -> None:
        self._jwks: dict | None = None
        self._jwks_fetched_at: float | None = None

    def _jwks_url(self) -> str:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL not configured")
        base = settings.supabase_url.rstrip("/")
        return f"{base}/auth/v1/.well-known/jwks.json"

    def _expected_issuer(self) -> str:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL not configured")
        base = settings.supabase_url.rstrip("/")
        return f"{base}/auth/v1"

    async def _get_jwks(self) -> dict:
        now = time.time()
        if self._jwks and self._jwks_fetched_at and (now - self._jwks_fetched_at) < 3600:
            return self._jwks

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self._jwks_url())
            resp.raise_for_status()
            self._jwks = resp.json()
            self._jwks_fetched_at = now
            return self._jwks

    async def verify(self, token: str) -> SupabasePrincipal:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL not configured")
        if not settings.supabase_anon_key:
            raise RuntimeError("SUPABASE_ANON_KEY not configured")

        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise JWTError("Missing kid")

        jwks = await self._get_jwks()
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        if not key:
            raise JWTError("Unknown kid")

        claims = jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.supabase_jwt_audience,
            issuer=self._expected_issuer(),
            options={"verify_aud": True, "verify_iss": True},
        )

        # Roles must come from app_metadata (server-controlled), not user_metadata.
        app_metadata = claims.get("app_metadata") or {}
        raw_roles = app_metadata.get("roles") or app_metadata.get("role") or []
        if isinstance(raw_roles, str):
            roles = {raw_roles}
        else:
            roles = {str(r) for r in raw_roles}

        return SupabasePrincipal(
            sub=str(claims.get("sub")),
            email=claims.get("email"),
            roles=roles,
            raw_claims=claims,
        )


supabase_jwt_verifier = SupabaseJWTVerifier()
