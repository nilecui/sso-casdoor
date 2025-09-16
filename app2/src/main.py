import os
import secrets
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from common.src.config import load_app2_config
from common.src.oidc import OIDCClient


app = FastAPI(title="App2")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

_cfg = load_app2_config()
_oidc = OIDCClient(_cfg.issuer, _cfg.client_id, _cfg.client_secret, _cfg.redirect_uri)


@app.get("/")
async def root(request: Request):
    portal_url = _portal_url(request)
    return templates.TemplateResponse("index.html", {"request": request, "portal_url": portal_url})


def _abs_callback_url(request: Request, path: str) -> str:
    scheme = request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.client.host
    return f"{scheme}://{host}{path}"


def _portal_url(request: Request) -> str:
    env_url = os.getenv("PORTAL_BASE_URL")
    if env_url:
        return env_url.rstrip("/") + "/"
    scheme = request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.client.host
    base_host = host.split(":")[0]
    return f"{scheme}://{base_host}:9000/"


@app.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    redirect_uri = _abs_callback_url(request, "/callback")
    url = await _oidc.build_authorize_url(state, redirect_uri=redirect_uri)
    return RedirectResponse(url)


@app.get("/callback")
async def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    if not code:
        return RedirectResponse("/")
    redirect_uri = _abs_callback_url(request, "/callback")
    token = await _oidc.exchange_code(code, redirect_uri=redirect_uri)
    access_token = token.get("access_token")
    user = {}
    if access_token:
        try:
            user = await _oidc.fetch_userinfo(access_token)
        except Exception:
            user = {}
    portal_url = _portal_url(request)
    return templates.TemplateResponse("protected.html", {"request": request, "user": user, "token": token, "portal_url": portal_url})


