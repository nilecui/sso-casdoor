import os
import secrets
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from common.src.config import load_portal_config
from common.src.oidc import OIDCClient
from .session import SessionManager


app = FastAPI(title="Portal")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

_cfg = load_portal_config()
_oidc = OIDCClient(_cfg.issuer, _cfg.client_id, _cfg.client_secret, _cfg.redirect_uri)
_session = SessionManager(_cfg.cookie_secret, _cfg.cookie_secure, _cfg.cookie_domain or "")


@app.get("/")
async def index(request: Request):
    sess = _session.get_session(request) or {}
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": sess.get("user"),
            "logged_in": bool(sess.get("user")),
        },
    )


def _abs_callback_url(request: Request, path: str) -> str:
    scheme = request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.client.host
    return f"{scheme}://{host}{path}"


@app.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    redirect_uri = _abs_callback_url(request, "/callback")
    auth_url = await _oidc.build_authorize_url(state, redirect_uri=redirect_uri)
    # 在真正返回给浏览器的重定向响应上设置 cookie，避免被覆盖
    response = RedirectResponse(url=auth_url)
    _session.set_session(response, {"state": state})
    return response


@app.get("/callback")
async def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    sess = _session.get_session(request) or {}
    saved_state = sess.get("state")
    if not code or not state or state != saved_state:
        # 清理无效会话并回首页
        response = RedirectResponse("/")
        _session.clear_session(response)
        return response
    redirect_uri = _abs_callback_url(request, "/callback")
    token = await _oidc.exchange_code(code, redirect_uri=redirect_uri)
    id_token = token.get("id_token")
    access_token = token.get("access_token")
    claims = {}
    try:
        if id_token:
            claims = await _oidc.verify_id_token(id_token)
    except Exception:
        pass
    userinfo = {}
    if access_token:
        try:
            userinfo = await _oidc.fetch_userinfo(access_token)
        except Exception:
            userinfo = {}
    user = userinfo or claims

    response = RedirectResponse(url="/")
    _session.set_session(response, {"user": user, "access_token": access_token, "id_token": id_token})
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    _session.clear_session(response)
    return response


@app.get("/to/app1")
async def to_app1(request: Request):
    scheme = request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.client.host
    # 将 host 的端口替换为 9001
    base_host = host.split(":")[0]
    target = f"{scheme}://{base_host}:9001/login"
    return RedirectResponse(target)


@app.get("/to/app2")
async def to_app2(request: Request):
    scheme = request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.client.host
    base_host = host.split(":")[0]
    target = f"{scheme}://{base_host}:9002/login"
    return RedirectResponse(target)


