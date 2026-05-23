"""Page-related tools for Plane MCP Server."""

import os
from typing import Any

from fastmcp import FastMCP

from plane_mcp.page_session import make_page_request


def _workspace_slug() -> str:
    workspace_slug = os.getenv("PLANE_WORKSPACE_SLUG", "")
    if not workspace_slug:
        raise RuntimeError(
            "PLANE_WORKSPACE_SLUG environment variable is required for page operations. "
            "Please set it to your workspace slug."
        )
    return workspace_slug


def _project_pages_path(project_id: str, suffix: str = "") -> str:
    suffix = suffix.lstrip("/")
    base = f"workspaces/{_workspace_slug()}/projects/{project_id}/pages"
    return f"{base}/{suffix}" if suffix else f"{base}/"


def _workspace_pages_path(suffix: str = "") -> str:
    suffix = suffix.lstrip("/")
    base = f"workspaces/{_workspace_slug()}/pages"
    return f"{base}/{suffix}" if suffix else f"{base}/"


def _favorite_pages_path(project_id: str, page_id: str) -> str:
    return f"workspaces/{_workspace_slug()}/projects/{project_id}/favorite-pages/{page_id}/"


def _simplify_page(page: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "name",
        "owned_by",
        "access",
        "is_locked",
        "is_favorite",
        "parent",
        "archived_at",
        "created_at",
        "updated_at",
    )
    return {key: page.get(key) for key in keys if key in page}


def _page_payload(
    name: str | None = None,
    description_html: str | None = None,
    access: int | None = None,
    color: str | None = None,
    parent: str | None = None,
    is_locked: bool | None = None,
    archived_at: str | None = None,
    view_props: dict[str, Any] | None = None,
    logo_props: dict[str, Any] | None = None,
    external_id: str | None = None,
    external_source: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    values = {
        "name": name,
        "description_html": description_html,
        "access": access,
        "color": color,
        "parent": parent,
        "is_locked": is_locked,
        "archived_at": archived_at,
        "view_props": view_props,
        "logo_props": logo_props,
        "external_id": external_id,
        "external_source": external_source,
    }
    for key, value in values.items():
        if value is not None:
            payload[key] = value
    return payload


def register_page_tools(mcp: FastMCP) -> None:
    """Register all page-related tools with the MCP server."""

    @mcp.tool()
    def list_pages(project_id: str) -> list[dict[str, Any]]:
        """
        List all pages in a project.

        Args:
            project_id: UUID of the project

        Returns:
            List of project pages
        """
        pages = make_page_request("GET", _project_pages_path(project_id))
        if isinstance(pages, list):
            return [_simplify_page(page) if isinstance(page, dict) else {"value": page} for page in pages]
        return pages

    @mcp.tool()
    def get_page(project_id: str, page_id: str) -> dict[str, Any]:
        """
        Get details of a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page

        Returns:
            Page details
        """
        return make_page_request("GET", _project_pages_path(project_id, f"{page_id}/"))

    @mcp.tool()
    def retrieve_project_page(project_id: str, page_id: str) -> dict[str, Any]:
        """
        Retrieve a project page by ID.

        Args:
            project_id: UUID of the project
            page_id: UUID of the page

        Returns:
            Page details
        """
        return get_page(project_id=project_id, page_id=page_id)

    @mcp.tool()
    def retrieve_workspace_page(page_id: str) -> dict[str, Any]:
        """
        Retrieve a workspace page by ID.

        Args:
            page_id: UUID of the page

        Returns:
            Page details
        """
        return make_page_request("GET", _workspace_pages_path(f"{page_id}/"))

    @mcp.tool()
    def create_page(
        project_id: str,
        name: str,
        description_html: str | None = None,
        access: int | None = None,
        color: str | None = None,
        parent: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new page in a project.

        Args:
            project_id: UUID of the project
            name: Page name
            description_html: HTML content for the page
            access: Page access level, typically 0 public or 1 private
            color: Page color
            parent: Optional parent page UUID

        Returns:
            Created page
        """
        payload = _page_payload(
            name=name,
            description_html=description_html,
            access=access,
            color=color,
            parent=parent,
        )
        return make_page_request("POST", _project_pages_path(project_id), payload)

    @mcp.tool()
    def create_project_page(
        project_id: str,
        name: str,
        description_html: str | None = None,
        access: int | None = None,
        color: str | None = None,
        is_locked: bool | None = None,
        archived_at: str | None = None,
        view_props: dict[str, Any] | None = None,
        logo_props: dict[str, Any] | None = None,
        external_id: str | None = None,
        external_source: str | None = None,
        parent: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a project page.

        Args:
            project_id: UUID of the project
            name: Page name
            description_html: HTML content for the page
            access: Page access level, typically 0 public or 1 private
            color: Page color
            is_locked: Whether the page is locked
            archived_at: Archive timestamp
            view_props: View properties
            logo_props: Logo properties
            external_id: External system ID
            external_source: External system source
            parent: Optional parent page UUID

        Returns:
            Created page
        """
        payload = _page_payload(
            name=name,
            description_html=description_html,
            access=access,
            color=color,
            parent=parent,
            is_locked=is_locked,
            archived_at=archived_at,
            view_props=view_props,
            logo_props=logo_props,
            external_id=external_id,
            external_source=external_source,
        )
        return make_page_request("POST", _project_pages_path(project_id), payload)

    @mcp.tool()
    def create_workspace_page(
        name: str,
        description_html: str | None = None,
        access: int | None = None,
        color: str | None = None,
        is_locked: bool | None = None,
        archived_at: str | None = None,
        view_props: dict[str, Any] | None = None,
        logo_props: dict[str, Any] | None = None,
        external_id: str | None = None,
        external_source: str | None = None,
        parent: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a workspace page.

        Args:
            name: Page name
            description_html: HTML content for the page
            access: Page access level, typically 0 public or 1 private
            color: Page color
            is_locked: Whether the page is locked
            archived_at: Archive timestamp
            view_props: View properties
            logo_props: Logo properties
            external_id: External system ID
            external_source: External system source
            parent: Optional parent page UUID

        Returns:
            Created page
        """
        payload = _page_payload(
            name=name,
            description_html=description_html,
            access=access,
            color=color,
            parent=parent,
            is_locked=is_locked,
            archived_at=archived_at,
            view_props=view_props,
            logo_props=logo_props,
            external_id=external_id,
            external_source=external_source,
        )
        return make_page_request("POST", _workspace_pages_path(), payload)

    @mcp.tool()
    def update_page(
        project_id: str,
        page_id: str,
        name: str | None = None,
        description_html: str | None = None,
        access: int | None = None,
        color: str | None = None,
        parent: str | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page
            name: Page name
            description_html: HTML content for the page
            access: Page access level, typically 0 public or 1 private
            color: Page color
            parent: Optional parent page UUID

        Returns:
            Updated page
        """
        payload = _page_payload(
            name=name,
            description_html=description_html,
            access=access,
            color=color,
            parent=parent,
        )
        return make_page_request("PATCH", _project_pages_path(project_id, f"{page_id}/"), payload)

    @mcp.tool()
    def delete_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Delete a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to delete

        Returns:
            Confirmation message with the deleted page ID
        """
        make_page_request("DELETE", _project_pages_path(project_id, f"{page_id}/"))
        return {"message": "Page deleted successfully", "page_id": page_id}

    @mcp.tool()
    def archive_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Archive a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to archive

        Returns:
            Confirmation message
        """
        make_page_request("POST", _project_pages_path(project_id, f"{page_id}/archive/"))
        return {"message": "Page archived successfully", "page_id": page_id}

    @mcp.tool()
    def unarchive_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Unarchive a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to unarchive

        Returns:
            Confirmation message
        """
        make_page_request("DELETE", _project_pages_path(project_id, f"{page_id}/archive/"))
        return {"message": "Page unarchived successfully", "page_id": page_id}

    @mcp.tool()
    def lock_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Lock a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to lock

        Returns:
            Confirmation message
        """
        make_page_request("POST", _project_pages_path(project_id, f"{page_id}/lock/"))
        return {"message": "Page locked successfully", "page_id": page_id}

    @mcp.tool()
    def unlock_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Unlock a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to unlock

        Returns:
            Confirmation message
        """
        make_page_request("DELETE", _project_pages_path(project_id, f"{page_id}/lock/"))
        return {"message": "Page unlocked successfully", "page_id": page_id}

    @mcp.tool()
    def favorite_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Mark a project page as favorite.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to favorite

        Returns:
            Confirmation message
        """
        make_page_request("POST", _favorite_pages_path(project_id, page_id))
        return {"message": "Page marked as favorite", "page_id": page_id}

    @mcp.tool()
    def unfavorite_page(project_id: str, page_id: str) -> dict[str, str]:
        """
        Remove a project page from favorites.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to unfavorite

        Returns:
            Confirmation message
        """
        make_page_request("DELETE", _favorite_pages_path(project_id, page_id))
        return {"message": "Page removed from favorites", "page_id": page_id}

    @mcp.tool()
    def duplicate_page(project_id: str, page_id: str) -> dict[str, Any]:
        """
        Duplicate a project page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page to duplicate

        Returns:
            Duplicated page
        """
        return make_page_request("POST", _project_pages_path(project_id, f"{page_id}/duplicate/"))

    @mcp.tool()
    def set_page_access(project_id: str, page_id: str, access: int) -> dict[str, Any]:
        """
        Set page access level.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page
            access: Access level, typically 0 public or 1 private

        Returns:
            Updated page
        """
        return make_page_request("POST", _project_pages_path(project_id, f"{page_id}/access/"), {"access": access})

    @mcp.tool()
    def get_pages_summary(project_id: str) -> list[dict[str, Any]]:
        """
        Get a summary view of project pages.

        Args:
            project_id: UUID of the project

        Returns:
            Page summary list
        """
        return make_page_request("GET", f"workspaces/{_workspace_slug()}/projects/{project_id}/pages-summary/")

    @mcp.tool()
    def get_page_description(project_id: str, page_id: str) -> dict[str, Any]:
        """
        Get a page description.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page

        Returns:
            Page description payload
        """
        return make_page_request("GET", _project_pages_path(project_id, f"{page_id}/description/"))

    @mcp.tool()
    def update_page_description(project_id: str, page_id: str, description_html: str) -> dict[str, Any]:
        """
        Update a page description.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page
            description_html: HTML content for the page description

        Returns:
            Updated page description payload
        """
        return make_page_request(
            "PATCH",
            _project_pages_path(project_id, f"{page_id}/description/"),
            {"description_html": description_html},
        )

    @mcp.tool()
    def get_page_versions(project_id: str, page_id: str) -> list[dict[str, Any]]:
        """
        Get version history for a page.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page

        Returns:
            Page versions
        """
        return make_page_request("GET", _project_pages_path(project_id, f"{page_id}/versions/"))

    @mcp.tool()
    def get_page_version(project_id: str, page_id: str, version_id: str) -> dict[str, Any]:
        """
        Get a specific page version.

        Args:
            project_id: UUID of the project containing the page
            page_id: UUID of the page
            version_id: UUID of the page version

        Returns:
            Page version
        """
        return make_page_request("GET", _project_pages_path(project_id, f"{page_id}/versions/{version_id}/"))
