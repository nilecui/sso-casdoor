import time
import json
import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from jose import jwt


class OIDCDiscovery:
    def __init__(self, issuer: str) -> None:
        self.issuer = issuer.rstrip("/")
        self._cache: Optional[Dict[str, Any]] = None
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_ts: float = 0.0

    async def get_config(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        url = f"{self.issuer}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            self._cache = resp.json()
        return self._cache

    async def get_jwks(self) -> Dict[str, Any]:
        # Cache JWKS for 5 minutes
        if self._jwks_cache and (time.time() - self._jwks_cache_ts) < 300:
            return self._jwks_cache
        conf = await self.get_config()
        jwks_uri = conf.get("jwks_uri")
        if not jwks_uri:
            # Fallback for Casdoor
            jwks_uri = f"{self.issuer}/.well-known/jwks"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(jwks_uri)
            resp.raise_for_status()
            self._jwks_cache = resp.json()
            self._jwks_cache_ts = time.time()
        return self._jwks_cache


class OIDCClient:
    def __init__(self, issuer: str, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.issuer = issuer.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.discovery = OIDCDiscovery(self.issuer)

    async def build_authorize_url(self, state: str, scope: str = "openid profile email", redirect_uri: Optional[str] = None) -> str:
        conf = await self.discovery.get_config()
        auth_endpoint = conf.get("authorization_endpoint") or f"{self.issuer}/login/oauth/authorize"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "state": state,
        }
        return f"{auth_endpoint}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        conf = await self.discovery.get_config()
        token_endpoint = conf.get("token_endpoint") or f"{self.issuer}/api/login/oauth/access_token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(token_endpoint, data=data, headers={"Accept": "application/json"})
            resp.raise_for_status()
            token = resp.json()
        # Normalize token fields
        token.setdefault("token_type", token.get("token_type", "Bearer"))
        return token

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        conf = await self.discovery.get_config()
        jwks = await self.discovery.get_jwks()
        # jose expects jwks as dict with 'keys'
        keys = jwks if "keys" in jwks else {"keys": jwks}
        try:
            claims = jwt.decode(
                id_token,
                keys,
                algorithms=[alg for alg in ["RS256", "RS512", "ES256", "ES384"]],
                audience=self.client_id,
                issuer=conf.get("issuer", self.issuer),
                options={"verify_at_hash": False},
            )
            return claims
        except Exception as exc:
            raise ValueError(f"Invalid ID token: {exc}")

    async def fetch_userinfo(self, access_token: str) -> Dict[str, Any]:
        conf = await self.discovery.get_config()
        userinfo_endpoint = conf.get("userinfo_endpoint") or f"{self.issuer}/api/userinfo"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"})
            resp.raise_for_status()
            return resp.json()


