from itsdangerous import URLSafeSerializer, BadSignature
from typing import Optional, Dict, Any
from fastapi import Request, Response


class SessionManager:
    def __init__(self, secret: str, cookie_secure: bool = False, cookie_domain: str = "", cookie_name: str = "app2_session") -> None:
        self.serializer = URLSafeSerializer(secret_key=secret, salt="app2-session")
        self.cookie_secure = cookie_secure
        self.cookie_domain = cookie_domain or None
        self.cookie_name = cookie_name

    def set_session(self, response: Response, data: Dict[str, Any]) -> None:
        token = self.serializer.dumps(data)
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=True,
            secure=self.cookie_secure,
            samesite="lax",
            domain=self.cookie_domain,
            path="/",
        )

    def clear_session(self, response: Response) -> None:
        response.delete_cookie(self.cookie_name, domain=self.cookie_domain or None, path="/")

    def get_session(self, request: Request) -> Optional[Dict[str, Any]]:
        raw = request.cookies.get(self.cookie_name)
        if not raw:
            return None
        try:
            return self.serializer.loads(raw)
        except BadSignature:
            return None


