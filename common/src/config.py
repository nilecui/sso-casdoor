from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class BaseAppConfig:
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    cookie_secure: bool
    cookie_domain: Optional[str]
    cookie_secret: str


def _get_env(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing environment variable: {key}")
    return value


def _get_bool(key: str, default: str = "false") -> bool:
    val = os.getenv(key, default).strip().lower()
    return val in {"1", "true", "yes", "on"}


def _base() -> dict:
    return {
        "issuer": _get_env("CASDOOR_ISSUER"),
        "cookie_secure": _get_bool("COOKIE_SECURE", "false"),
        "cookie_domain": os.getenv("COOKIE_DOMAIN", None) or None,
        "cookie_secret": os.getenv("COOKIE_SECRET", "dev-secret-change-me"),
    }


def load_portal_config() -> BaseAppConfig:
    base = _base()
    return BaseAppConfig(
        issuer=base["issuer"],
        client_id=_get_env("PORTAL_CLIENT_ID"),
        client_secret=_get_env("PORTAL_CLIENT_SECRET"),
        redirect_uri=_get_env("PORTAL_REDIRECT_URI"),
        cookie_secure=base["cookie_secure"],
        cookie_domain=base["cookie_domain"],
        cookie_secret=base["cookie_secret"],
    )


def load_app1_config() -> BaseAppConfig:
    base = _base()
    return BaseAppConfig(
        issuer=base["issuer"],
        client_id=_get_env("APP1_CLIENT_ID"),
        client_secret=_get_env("APP1_CLIENT_SECRET"),
        redirect_uri=_get_env("APP1_REDIRECT_URI"),
        cookie_secure=base["cookie_secure"],
        cookie_domain=base["cookie_domain"],
        cookie_secret=base["cookie_secret"],
    )


def load_app2_config() -> BaseAppConfig:
    base = _base()
    return BaseAppConfig(
        issuer=base["issuer"],
        client_id=_get_env("APP2_CLIENT_ID"),
        client_secret=_get_env("APP2_CLIENT_SECRET"),
        redirect_uri=_get_env("APP2_REDIRECT_URI"),
        cookie_secure=base["cookie_secure"],
        cookie_domain=base["cookie_domain"],
        cookie_secret=base["cookie_secret"],
    )


