import os
import secrets
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from common.src.config import load_app2_config
from common.src.oidc import OIDCClient
from itsdangerous import URLSafeSerializer, BadSignature
from .session import SessionManager


app = FastAPI(title="App2")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

_cfg = load_app2_config()
_oidc = OIDCClient(_cfg.issuer, _cfg.client_id, _cfg.client_secret, _cfg.redirect_uri, _cfg.organization_name, _cfg.application_name)
_session = SessionManager(_cfg.cookie_secret, _cfg.cookie_secure, _cfg.cookie_domain or "", cookie_name="app2_session")


@app.get("/")
async def root(request: Request):
    sess = _session.get_session(request) or {}
    portal_url = _portal_url(request)
    
    # 检查是否有SSO token参数
    sso_token = request.query_params.get("sso_token")
    
    if sso_token:
        # 验证SSO token
        try:
            user_info = await _oidc.fetch_userinfo(sso_token)
            if user_info:
                # Token有效，保存用户会话
                user = {
                    "username": user_info.get("username") or user_info.get("preferred_username"),
                    "name": user_info.get("name"),
                    "email": user_info.get("email"),
                    "sub": user_info.get("sub"),
                }
                
                response = templates.TemplateResponse("protected.html", {
                    "request": request, 
                    "portal_url": portal_url, 
                    "user": user
                })
                _session.set_session(response, {"user": user, "access_token": sso_token})
                print(f"SSO Token验证成功，用户: {user.get('username')}")
                return response
        except Exception as e:
            print(f"SSO Token验证失败: {e}")
            # Token无效，继续正常流程
    
    if sess.get("user"):
        # 已登录，显示受保护页面
        return templates.TemplateResponse("protected.html", {"request": request, "portal_url": portal_url, "user": sess.get("user")})
    else:
        # 未登录，显示登录页面
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
async def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        redirect_uri = _abs_callback_url(request, "/callback")
        url = await _oidc.build_authorize_url(secrets.token_urlsafe(16), redirect_uri=redirect_uri)
        return RedirectResponse(url)
    if not code:
        return RedirectResponse("/")
    if state:
        try:
            s = URLSafeSerializer(_cfg.client_secret, salt="oidc-state")
            _ = s.loads(state)
        except BadSignature:
            pass
    redirect_uri = _abs_callback_url(request, "/callback")
    token = await _oidc.exchange_code(code, redirect_uri=redirect_uri)
    access_token = token.get("access_token")
    user = {}
    if access_token:
        try:
            info = await _oidc.fetch_userinfo(access_token)
            user = {
                "username": info.get("username") or info.get("preferred_username"),
                "name": info.get("name"),
                "email": info.get("email"),
                "sub": info.get("sub"),
            }
        except Exception:
            user = {}
    response = RedirectResponse("/")
    _session.set_session(response, {"user": user})
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    _session.clear_session(response)
    return response


