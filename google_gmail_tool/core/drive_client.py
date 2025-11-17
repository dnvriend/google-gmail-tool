"""Google Drive API client for listing and downloading files.

This module provides a client for interacting with the Google Drive API v3.
Supports read-only operations including listing files, searching, downloading,
and retrieving metadata.

Design:
- CLI-independent, importable library
- Type-safe with strict mypy compliance
- Exception-based error handling
- Comprehensive logging for observability

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import io
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]
from googleapiclient.http import MediaIoBaseDownload  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class DriveClient:
    """Client for interacting with Google Drive API v3 (read-only operations)."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Drive client.

        Args:
            credentials: OAuth2 credentials for Drive API access (drive.readonly scope)
        """
        self.credentials = credentials
        self.service = build("drive", "v3", credentials=credentials)
        logger.debug("Drive API service initialized")

    def list_files(
        self,
        query: str | None = None,
        max_results: int = 100,
        order_by: str = "modifiedTime desc",
        folder_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List files in Google Drive with optional filtering.

        Args:
            query: Drive API query string (e.g., "mimeType='application/pdf'")
            max_results: Maximum number of files to return (default 100, max 1000)
            order_by: Sort order (e.g., "modifiedTime desc", "name", "createdTime")
            folder_id: If specified, list files only in this folder

        Returns:
            List of file dictionaries with metadata (id, name, mimeType, size, etc.)

        Raises:
            Exception: If Drive API call fails

        Example:
            >>> client = DriveClient(credentials)
            >>> files = client.list_files(query="name contains 'report'", max_results=10)
            >>> for file in files:
            ...     print(f"{file['name']} ({file['mimeType']})")
        """
        logger.info(
            f"Listing files: query={query}, max_results={max_results}, "
            f"order_by={order_by}, folder_id={folder_id}"
        )

        # Validate max_results
        if max_results > 1000:
            logger.warning(
                f"max_results {max_results} exceeds Drive API limit, capping at 1000"
            )
            max_results = 1000

        # Build query
        queries = []
        if query:
            queries.append(query)
        if folder_id:
            queries.append(f"'{folder_id}' in parents")

        final_query = " and ".join(queries) if queries else None

        if final_query:
            logger.debug(f"Using Drive query: {final_query}")

        # Build request parameters
        params: dict[str, Any] = {
            "pageSize": min(max_results, 100),  # API max per page is 100
            "fields": "nextPageToken, files(id, name, mimeType, size, createdTime, "
            "modifiedTime, webViewLink, iconLink, parents, shared, owners, "
            "permissions, trashed)",
            "orderBy": order_by,
        }
        if final_query:
            params["q"] = final_query

        try:
            files = []
            page_token = None

            # Paginate through results
            while len(files) < max_results:
                if page_token:
                    params["pageToken"] = page_token

                logger.debug(f"Calling Drive API: files().list() (page {len(files)//100 + 1})")
                response = self.service.files().list(**params).execute()

                batch = response.get("files", [])
                files.extend(batch)
                logger.debug(f"Retrieved {len(batch)} files in this batch")

                # Check if there are more pages
                page_token = response.get("nextPageToken")
                if not page_token or len(files) >= max_results:
                    break

            # Trim to max_results
            files = files[:max_results]

            logger.info(f"Successfully retrieved {len(files)} files")
            return files

        except Exception as e:
            logger.error(f"Failed to list files: {type(e).__name__}: {e}")
            raise

    def get_file(self, file_id: str) -> dict[str, Any]:
        """Get metadata for a specific file.

        Args:
            file_id: The Drive file ID

        Returns:
            Dictionary with file metadata

        Raises:
            Exception: If file not found or API call fails

        Example:
            >>> client = DriveClient(credentials)
            >>> file = client.get_file("1abc123xyz")
            >>> print(f"{file['name']} - {file['mimeType']}")
        """
        logger.info(f"Getting file metadata: {file_id}")

        try:
            file = (
                self.service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, "
                    "webViewLink, iconLink, parents, shared, owners, permissions, "
                    "trashed, description",
                )
                .execute()
            )
            logger.info(f"Retrieved metadata for file: {file.get('name')}")
            return file

        except Exception as e:
            logger.error(f"Failed to get file {file_id}: {type(e).__name__}: {e}")
            raise

    def download_file(self, file_id: str, output_path: str) -> int:
        """Download a file from Google Drive.

        Args:
            file_id: The Drive file ID
            output_path: Local path to save the file

        Returns:
            Number of bytes downloaded

        Raises:
            Exception: If download fails or file not found

        Example:
            >>> client = DriveClient(credentials)
            >>> bytes_downloaded = client.download_file("1abc123xyz", "/tmp/file.pdf")
            >>> print(f"Downloaded {bytes_downloaded} bytes")
        """
        logger.info(f"Downloading file {file_id} to {output_path}")

        try:
            # Get file metadata first
            file_metadata = self.get_file(file_id)
            mime_type = file_metadata.get("mimeType", "")

            # Check if it's a Google Workspace file (needs export)
            if mime_type.startswith("application/vnd.google-apps."):
                logger.warning(
                    f"File is a Google Workspace document ({mime_type}). "
                    "Use export_file() instead for format conversion."
                )
                raise ValueError(
                    f"Cannot download Google Workspace files directly. "
                    f"File type: {mime_type}. Use export_file() with a target format."
                )

            # Download binary file
            request = self.service.files().get_media(fileId=file_id)
            file_handle = io.FileIO(output_path, "wb")
            downloader = MediaIoBaseDownload(file_handle, request)

            done = False
            bytes_downloaded = 0
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    bytes_downloaded = int(status.resumable_progress)
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            file_handle.close()
            logger.info(f"Successfully downloaded {bytes_downloaded} bytes to {output_path}")
            return bytes_downloaded

        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {type(e).__name__}: {e}")
            raise

    def search_files(
        self,
        name_contains: str | None = None,
        mime_type: str | None = None,
        folder_id: str | None = None,
        shared_with_me: bool = False,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Search for files with common filters.

        Args:
            name_contains: Search for files with name containing this text
            mime_type: Filter by MIME type (e.g., 'application/pdf', 'image/jpeg')
            folder_id: Search only within this folder
            shared_with_me: Only show files shared with me
            max_results: Maximum number of results to return

        Returns:
            List of file dictionaries matching the search criteria

        Raises:
            Exception: If search fails

        Example:
            >>> client = DriveClient(credentials)
            >>> pdfs = client.search_files(name_contains="report", mime_type="application/pdf")
            >>> for file in pdfs:
            ...     print(file['name'])
        """
        logger.info(
            f"Searching files: name_contains={name_contains}, mime_type={mime_type}, "
            f"folder_id={folder_id}, shared_with_me={shared_with_me}"
        )

        # Build query parts
        query_parts = []

        if name_contains:
            # Escape single quotes in search term
            escaped_name = name_contains.replace("'", "\\'")
            query_parts.append(f"name contains '{escaped_name}'")

        if mime_type:
            query_parts.append(f"mimeType='{mime_type}'")

        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")

        if shared_with_me:
            query_parts.append("sharedWithMe=true")

        # Always exclude trashed files
        query_parts.append("trashed=false")

        query = " and ".join(query_parts)
        logger.debug(f"Search query: {query}")

        return self.list_files(query=query, max_results=max_results)
