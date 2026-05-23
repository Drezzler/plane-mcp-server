"""Authentication tools for Plane session-backed APIs."""

import os
from typing import Any

from fastmcp import FastMCP

from plane_mcp.page_session import authenticate_with_password, import_cookies, is_session_authenticated, reset_session


def register_auth_tools(mcp: FastMCP) -> None:
    """Register session authentication tools used by Plane page APIs."""

    @mcp.tool()
    def plane_login(email: str, password: str, host: str | None = None) -> dict[str, Any]:
        """
        Authenticate with Plane using email/password for session-backed page APIs.

        Args:
            email: Plane account email
            password: Plane account password
            host: Optional Plane host URL. Defaults to PLANE_BASE_URL.

        Returns:
            Authentication status and details
        """
        result = authenticate_with_password(email=email, password=password, host=host)
        if result.get("success"):
            return {
                "message": "Successfully authenticated with Plane",
                "authenticated": True,
                "note": "Session authentication enables Plane page APIs.",
                **result,
            }
        return {
            "message": "Authentication failed",
            "authenticated": False,
            **result,
        }

    @mcp.tool()
    def plane_import_cookies(cookies_json: str, host: str | None = None) -> dict[str, Any]:
        """
        Import browser-exported Plane cookies for session-backed page APIs.

        Args:
            cookies_json: JSON string containing exported browser cookies
            host: Optional Plane host URL. Defaults to PLANE_BASE_URL.

        Returns:
            Cookie import and authentication status
        """
        result = import_cookies(cookies_json=cookies_json, host=host)
        if result.get("success"):
            return {
                "message": "Successfully imported Plane browser cookies",
                "authenticated": True,
                **result,
            }
        return {
            "message": "Failed to import Plane browser cookies",
            "authenticated": False,
            **result,
        }

    @mcp.tool()
    def plane_auth_status() -> dict[str, Any]:
        """
        Check current Plane authentication status.

        Returns:
            Current session and API-key authentication status
        """
        authenticated = is_session_authenticated()
        has_api_key = bool(os.getenv("PLANE_API_KEY"))

        if authenticated and has_api_key:
            mode = "session + API key"
        elif authenticated:
            mode = "session"
        elif has_api_key:
            mode = "API key only"
        else:
            mode = "not authenticated"

        return {
            "session_authenticated": authenticated,
            "api_key_configured": has_api_key,
            "current_mode": mode,
            "note": (
                "Page APIs require session authentication via plane_login, plane_import_cookies, "
                "or PLANE_EMAIL/PLANE_PASSWORD."
            ),
        }

    @mcp.tool()
    def plane_logout() -> dict[str, Any]:
        """
        Clear Plane session cookies from this MCP server process.

        Returns:
            Logout status
        """
        reset_session()
        return {
            "message": "Successfully logged out",
            "authenticated": False,
        }
