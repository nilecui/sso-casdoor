import os
import secrets
import time
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from common.src.config import load_portal_config, load_app1_config, load_app2_config
from common.src.oidc import OIDCClient
from .session import SessionManager
from itsdangerous import URLSafeSerializer


app = FastAPI(title="Portal")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

_cfg = load_portal_config()
_oidc = OIDCClient(_cfg.issuer, _cfg.client_id, _cfg.client_secret, _cfg.redirect_uri, _cfg.organization_name, _cfg.application_name)
_session = SessionManager(_cfg.cookie_secret, _cfg.cookie_secure, _cfg.cookie_domain or "")

# For IdP-initiated SSO to apps
_app1_cfg = load_app1_config()
_app2_cfg = load_app2_config()
_oidc_app1 = OIDCClient(_app1_cfg.issuer, _app1_cfg.client_id, _app1_cfg.client_secret, _app1_cfg.redirect_uri, _app1_cfg.organization_name, _app1_cfg.application_name)
_oidc_app2 = OIDCClient(_app2_cfg.issuer, _app2_cfg.client_id, _app2_cfg.client_secret, _app2_cfg.redirect_uri, _app2_cfg.organization_name, _app2_cfg.application_name)


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
    # 只保留必要的轻量字段，避免 Cookie 过大
    base_user = userinfo or claims or {}
    user = {
        "username": base_user.get("username") or base_user.get("preferred_username"),
        "name": base_user.get("name"),
        "email": base_user.get("email"),
        "sub": base_user.get("sub"),
    }

    response = RedirectResponse(url="/")
    # 保存用户信息和tokens用于SSO
    _session.set_session(response, {
        "user": user, 
        "id_token": id_token,
        "access_token": access_token
    })
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    _session.clear_session(response)
    return response


def _abs_url(request: Request, port: int, path: str) -> str:
    scheme = request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.client.host
    base_host = host.split(":")[0]
    return f"{scheme}://{base_host}:{port}{path}"


@app.get("/to/app1")
async def to_app1(request: Request):
    # 检查用户是否已在门户登录
    sess = _session.get_session(request) or {}
    if not sess.get("user"):
        # 用户未登录，重定向到门户登录
        return RedirectResponse("/login")
    
    # 获取用户的access_token和id_token
    access_token = sess.get("access_token")
    id_token = sess.get("id_token")
    
    if not access_token:
        # 如果没有access_token，尝试静默授权获取
        s = URLSafeSerializer(_app1_cfg.client_secret, salt="oidc-state")
        state = s.dumps({"n": secrets.token_urlsafe(8), "ts": int(time.time())})
        
        redirect_uri = _abs_url(request, 9001, "/callback")
        extra = {"prompt": "none"}
        
        if id_token:
            extra["id_token_hint"] = id_token
        
        try:
            auth_url = await _oidc_app1.build_authorize_url(state, redirect_uri=redirect_uri, extra_params=extra)
            return RedirectResponse(auth_url)
        except Exception as e:
            print(f"静默登录失败: {e}")
            auth_url = await _oidc_app1.build_authorize_url(state, redirect_uri=redirect_uri)
            return RedirectResponse(auth_url)
    
    # 使用JWT Token传递方案：直接跳转到App1并传递token
    app1_url = _abs_url(request, 9001, "/")
    token_url = f"{app1_url}?sso_token={access_token}"
    
    print(f"使用JWT Token传递方案跳转到App1: {token_url}")
    return RedirectResponse(token_url)


@app.get("/to/app2")
async def to_app2(request: Request):
    # 检查用户是否已在门户登录
    sess = _session.get_session(request) or {}
    if not sess.get("user"):
        # 用户未登录，重定向到门户登录
        return RedirectResponse("/login")
    
    # 获取用户的access_token和id_token
    access_token = sess.get("access_token")
    id_token = sess.get("id_token")
    
    if not access_token:
        # 如果没有access_token，尝试静默授权获取
        s = URLSafeSerializer(_app2_cfg.client_secret, salt="oidc-state")
        state = s.dumps({"n": secrets.token_urlsafe(8), "ts": int(time.time())})
        
        redirect_uri = _abs_url(request, 9002, "/callback")
        extra = {"prompt": "none"}
        
        if id_token:
            extra["id_token_hint"] = id_token
        
        try:
            auth_url = await _oidc_app2.build_authorize_url(state, redirect_uri=redirect_uri, extra_params=extra)
            return RedirectResponse(auth_url)
        except Exception as e:
            print(f"静默登录失败: {e}")
            auth_url = await _oidc_app2.build_authorize_url(state, redirect_uri=redirect_uri)
            return RedirectResponse(auth_url)
    
    # 使用JWT Token传递方案：直接跳转到App2并传递token
    app2_url = _abs_url(request, 9002, "/")
    token_url = f"{app2_url}?sso_token={access_token}"
    
    print(f"使用JWT Token传递方案跳转到App2: {token_url}")
    return RedirectResponse(token_url)


