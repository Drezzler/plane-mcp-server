"""Session-authenticated Plane requests for page APIs."""

import json
import os
import time
from http.cookiejar import Cookie
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

SESSION_TIMEOUT_SECONDS = 3600
SESSION_COOKIE_NAMES = {"session-id", "sessionid", "plane_session"}
CSRF_COOKIE_NAMES = {"csrftoken", "csrf", "XSRF-TOKEN"}

_session: requests.Session | None = None
_authenticated_at: float | None = None


def get_plane_host(host: str | None = None) -> str:
    """Return the configured Plane host with one trailing slash."""
    base_url = host or os.getenv("PLANE_BASE_URL") or os.getenv("PLANE_API_HOST_URL") or "https://api.plane.so"
    return base_url.rstrip("/") + "/"


def get_session() -> requests.Session:
    """Return the process-local requests session used for Plane page APIs."""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def is_session_authenticated() -> bool:
    """Return whether the process-local Plane session is currently authenticated."""
    if _authenticated_at is None:
        return False
    if time.time() - _authenticated_at > SESSION_TIMEOUT_SECONDS:
        reset_session()
        return False
    return True


def reset_session() -> None:
    """Clear the process-local Plane session."""
    global _session, _authenticated_at
    if _session is not None:
        _session.cookies.clear()
    _session = None
    _authenticated_at = None


def _origin_headers(host: str) -> dict[str, str]:
    app_origin = "https://app.plane.so" if "api.plane.so" in host else host.rstrip("/")
    referer = "https://app.plane.so/" if "api.plane.so" in host else host
    return {
        "Origin": app_origin,
        "Referer": referer,
    }


def _find_cookie_value(names: set[str]) -> str | None:
    session = get_session()
    for cookie in session.cookies:
        if cookie.name in names:
            return cookie.value
    return None


def authenticate_with_password(email: str, password: str, host: str | None = None) -> dict[str, Any]:
    """Authenticate to Plane with email/password and store session cookies."""
    global _authenticated_at

    reset_session()
    session = get_session()
    base_url = get_plane_host(host)

    try:
        csrf_url = urljoin(base_url, "auth/get-csrf-token/")
        csrf_response = session.get(csrf_url, headers=_origin_headers(base_url), timeout=30)
        csrf_response.raise_for_status()

        csrf_token = _find_cookie_value(CSRF_COOKIE_NAMES)
        if not csrf_token:
            return {
                "success": False,
                "error": "csrf",
                "message": "CSRF token not found in Plane response.",
            }

        login_response = session.post(
            urljoin(base_url, "auth/sign-in/"),
            data={"email": email, "password": password},
            headers={
                **_origin_headers(base_url),
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": csrf_token,
            },
            allow_redirects=False,
            timeout=30,
        )
        if login_response.status_code not in range(200, 300) and login_response.status_code != 302:
            return {
                "success": False,
                "error": "credentials" if login_response.status_code in (401, 403) else "unknown",
                "message": f"Plane login failed with HTTP {login_response.status_code}.",
            }

        verify_response = session.get(urljoin(base_url, "api/users/me/"), timeout=30)
        if verify_response.status_code != 200:
            return {
                "success": False,
                "error": "credentials",
                "message": f"Could not verify Plane session, HTTP {verify_response.status_code}.",
            }

        _authenticated_at = time.time()
        has_standard_session_cookie = any(cookie.name in SESSION_COOKIE_NAMES for cookie in session.cookies)
        return {
            "success": True,
            "authenticated": True,
            "session_cookie_detected": has_standard_session_cookie,
        }
    except requests.RequestException as exc:
        reset_session()
        logger.warning("Plane session authentication failed: %s", exc)
        return {
            "success": False,
            "error": "network",
            "message": str(exc),
        }


def _make_cookie(raw: dict[str, Any], host: str) -> Cookie:
    domain = raw.get("domain") or urlparse(host).hostname or ""
    path = raw.get("path") or "/"
    name = raw.get("name") or raw.get("key")
    value = raw.get("value")
    if not name or value is None:
        raise ValueError("Cookie must include name/key and value")

    return Cookie(
        version=0,
        name=str(name),
        value=str(value),
        port=None,
        port_specified=False,
        domain=str(domain).lstrip("."),
        domain_specified=bool(domain),
        domain_initial_dot=str(domain).startswith("."),
        path=str(path),
        path_specified=True,
        secure=bool(raw.get("secure", False)),
        expires=raw.get("expirationDate") or raw.get("expires"),
        discard=False,
        comment=None,
        comment_url=None,
        rest={"HttpOnly": raw.get("httpOnly", False)},
        rfc2109=False,
    )


def import_cookies(cookies_json: str, host: str | None = None) -> dict[str, Any]:
    """Import browser-exported cookies and verify the Plane session."""
    global _authenticated_at

    base_url = get_plane_host(host)
    session = get_session()

    try:
        payload = json.loads(cookies_json)
        cookies = payload if isinstance(payload, list) else [payload]

        imported = 0
        for item in cookies:
            if isinstance(item, str):
                name, separator, value = item.partition("=")
                if not separator:
                    continue
                session.cookies.set_cookie(requests.cookies.create_cookie(name=name, value=value))
            elif isinstance(item, dict):
                session.cookies.set_cookie(_make_cookie(item, base_url))
            else:
                continue
            imported += 1

        if imported == 0:
            return {"success": False, "message": "No valid cookies found in JSON."}

        verify_response = session.get(urljoin(base_url, "api/users/me/"), timeout=30)
        if verify_response.status_code != 200:
            return {
                "success": False,
                "message": f"Imported cookies did not verify, HTTP {verify_response.status_code}.",
            }

        _authenticated_at = time.time()
        return {"success": True, "authenticated": True, "cookies_imported": imported}
    except (json.JSONDecodeError, ValueError, requests.RequestException) as exc:
        return {"success": False, "message": str(exc)}


def ensure_session_authenticated() -> None:
    """Ensure page APIs have a live session, optionally logging in from env credentials."""
    if is_session_authenticated():
        return

    email = os.getenv("PLANE_EMAIL")
    password = os.getenv("PLANE_PASSWORD")
    if email and password:
        result = authenticate_with_password(email, password)
        if result.get("success"):
            return

    raise RuntimeError(
        "Plane page APIs require session authentication. Call plane_login first, import cookies with "
        "plane_import_cookies, or set PLANE_EMAIL and PLANE_PASSWORD for automatic login."
    )


def make_page_request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    """Make a session-authenticated request to Plane's non-versioned page API."""
    ensure_session_authenticated()

    session = get_session()
    base_url = get_plane_host()
    url = urljoin(base_url, f"api/{path.lstrip('/')}")

    headers: dict[str, str] = {}
    if method.upper() != "GET":
        headers["Content-Type"] = "application/json"
        csrf_token = _find_cookie_value(CSRF_COOKIE_NAMES)
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token

    response = session.request(
        method=method.upper(),
        url=url,
        json=body if method.upper() != "GET" else None,
        headers=headers,
        timeout=30,
    )
    if response.status_code == 204:
        return None
    if 200 <= response.status_code < 300:
        if not response.content:
            return None
        if "application/json" in response.headers.get("content-type", "").lower():
            return response.json()
        return response.text

    try:
        details = response.json()
    except ValueError:
        details = response.text
    raise RuntimeError(f"Plane page API request failed: HTTP {response.status_code}: {details}")
