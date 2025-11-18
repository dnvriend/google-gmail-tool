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
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

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
            logger.warning(f"max_results {max_results} exceeds Drive API limit, capping at 1000")
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
            files: list[dict[str, Any]] = []
            page_token = None

            # Paginate through results
            while len(files) < max_results:
                if page_token:
                    params["pageToken"] = page_token

                logger.debug(f"Calling Drive API: files().list() (page {len(files) // 100 + 1})")
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
            file: dict[str, Any] = (
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

    def create_folder(
        self, name: str, parent_id: str | None = None, description: str | None = None
    ) -> dict[str, Any]:
        """Create a folder in Google Drive.

        Args:
            name: Name for the folder
            parent_id: ID of the parent folder (None = My Drive root)
            description: Optional description for the folder

        Returns:
            Dictionary with folder metadata (id, name, mimeType, webViewLink, etc.)

        Raises:
            ValueError: If folder with same name already exists in parent location
            Exception: If folder creation fails

        Examples:
            >>> client = DriveClient(credentials)
            >>> # Create folder in My Drive root
            >>> folder = client.create_folder("My Documents")
            >>> print(f"Created: {folder['name']} (ID: {folder['id']})")

            >>> # Create folder in specific parent with description
            >>> folder = client.create_folder(
            ...     "Reports",
            ...     parent_id="1abc123",
            ...     description="Monthly reports folder"
            ... )
        """
        logger.info(f"Creating folder: '{name}' in parent: {parent_id or 'root'}")

        # Check if folder with same name already exists in parent
        escaped_name = name.replace("'", "\\'")
        query_parts = [
            f"name='{escaped_name}'",
            "mimeType='application/vnd.google-apps.folder'",
            "trashed=false",
        ]
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")
        else:
            query_parts.append("'root' in parents")

        check_query = " and ".join(query_parts)
        logger.debug(f"Checking for existing folder with query: {check_query}")

        try:
            existing_folders = self.list_files(query=check_query, max_results=1)
            if existing_folders:
                error_msg = (
                    f"Folder with name '{name}' already exists in "
                    f"{'folder ' + parent_id if parent_id else 'My Drive root'}. "
                    f"Existing folder ID: {existing_folders[0]['id']}. "
                    f"Use a different name or rename the existing folder first."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        except ValueError:
            raise  # Re-raise ValueError from duplicate check
        except Exception as e:
            logger.warning(f"Could not check for existing folders: {type(e).__name__}: {e}")

        # Build folder metadata
        file_metadata: dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]
        if description:
            file_metadata["description"] = description

        try:
            # Create folder
            logger.debug(f"Creating folder: {name}")
            folder: dict[str, Any] = (
                self.service.files()
                .create(
                    body=file_metadata,
                    fields="id, name, mimeType, createdTime, modifiedTime, "
                    "webViewLink, iconLink, parents, description",
                )
                .execute()
            )

            logger.info(f"Successfully created folder: {folder['name']} (ID: {folder['id']})")
            return folder

        except Exception as e:
            logger.error(f"Failed to create folder '{name}': {type(e).__name__}: {e}")
            raise

    def rename_folder(self, folder_id: str, new_name: str) -> dict[str, Any]:
        """Rename a folder in Google Drive.

        This method is a convenience wrapper that verifies the item is a folder
        before calling rename_file().

        Args:
            folder_id: The Drive folder ID
            new_name: New name for the folder

        Returns:
            Dictionary with updated folder metadata

        Raises:
            ValueError: If the item is not a folder
            Exception: If rename fails or folder not found

        Examples:
            >>> client = DriveClient(credentials)
            >>> folder = client.rename_folder("1abc123xyz", "New Folder Name")
            >>> print(f"Renamed to: {folder['name']}")
        """
        logger.info(f"Renaming folder {folder_id} to '{new_name}'")

        try:
            # Verify it's a folder
            file_metadata = self.get_file(folder_id)
            if file_metadata.get("mimeType") != "application/vnd.google-apps.folder":
                item_name = file_metadata.get("name")
                error_msg = (
                    f"Item {folder_id} is not a folder "
                    f"(mimeType: {file_metadata.get('mimeType')}). "
                    f"This method only works with folders. The item name is: {item_name}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Update folder name
            folder_metadata = {"name": new_name}
            folder: dict[str, Any] = (
                self.service.files()
                .update(
                    fileId=folder_id,
                    body=folder_metadata,
                    fields="id, name, mimeType, modifiedTime, webViewLink, parents",
                )
                .execute()
            )

            logger.info(f"Successfully renamed folder {folder_id} to '{folder['name']}'")
            return folder

        except ValueError:
            raise  # Re-raise ValueError from validation
        except Exception as e:
            logger.error(f"Failed to rename folder {folder_id}: {type(e).__name__}: {e}")
            raise

    def move_folder(self, folder_id: str, destination_folder_id: str) -> dict[str, Any]:
        """Move a folder to a different parent folder in Google Drive.

        This method is a convenience wrapper that verifies the item is a folder
        before performing the move operation.

        Args:
            folder_id: The Drive folder ID to move
            destination_folder_id: ID of the destination parent folder

        Returns:
            Dictionary with updated folder metadata

        Raises:
            ValueError: If the item is not a folder
            Exception: If move fails or folder not found

        Examples:
            >>> client = DriveClient(credentials)
            >>> folder = client.move_folder("1abc123xyz", "1parent456")
            >>> print(f"Moved {folder['name']} to new parent")
        """
        logger.info(f"Moving folder {folder_id} to folder {destination_folder_id}")

        try:
            # Verify it's a folder
            file = (
                self.service.files()
                .get(fileId=folder_id, fields="parents, name, mimeType")
                .execute()
            )

            if file.get("mimeType") != "application/vnd.google-apps.folder":
                error_msg = (
                    f"Item {folder_id} is not a folder "
                    f"(mimeType: {file.get('mimeType')}). "
                    f"This method only works with folders. The item name is: {file.get('name')}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            previous_parents = ",".join(file.get("parents", []))
            folder_name = file.get("name", "unknown")

            logger.debug(
                f"Moving folder '{folder_name}' from parents [{previous_parents}] "
                f"to [{destination_folder_id}]"
            )

            # Move folder by adding new parent and removing old parents
            updated_folder: dict[str, Any] = (
                self.service.files()
                .update(
                    fileId=folder_id,
                    addParents=destination_folder_id,
                    removeParents=previous_parents,
                    fields="id, name, mimeType, modifiedTime, webViewLink, parents",
                )
                .execute()
            )

            logger.info(
                f"Successfully moved folder '{folder_name}' (ID: {folder_id}) "
                f"to folder {destination_folder_id}"
            )
            return updated_folder

        except ValueError:
            raise  # Re-raise ValueError from validation
        except Exception as e:
            logger.error(f"Failed to move folder {folder_id}: {type(e).__name__}: {e}")
            raise

    def delete_folder(self, folder_id: str, permanent: bool = False) -> None:
        """Delete a folder in Google Drive.

        This method is a convenience wrapper that verifies the item is a folder
        before performing the delete operation.

        Args:
            folder_id: The Drive folder ID
            permanent: If False (default), move to trash. If True, permanently delete.

        Raises:
            ValueError: If the item is not a folder
            Exception: If delete fails or folder not found

        Examples:
            >>> client = DriveClient(credentials)
            >>> # Move to trash (recoverable)
            >>> client.delete_folder("1abc123xyz")

            >>> # Permanently delete (irreversible, deletes contents)
            >>> client.delete_folder("1abc123xyz", permanent=True)
        """
        action = "Permanently deleting" if permanent else "Trashing"
        logger.info(f"{action} folder {folder_id}")

        try:
            # Verify it's a folder
            file_metadata = self.get_file(folder_id)
            if file_metadata.get("mimeType") != "application/vnd.google-apps.folder":
                item_name = file_metadata.get("name")
                error_msg = (
                    f"Item {folder_id} is not a folder "
                    f"(mimeType: {file_metadata.get('mimeType')}). "
                    f"This method only works with folders. The item name is: {item_name}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Delete folder
            if permanent:
                # Permanently delete
                self.service.files().delete(fileId=folder_id).execute()
                logger.info(f"Successfully permanently deleted folder {folder_id}")
            else:
                # Move to trash
                folder_metadata = {"trashed": True}
                self.service.files().update(fileId=folder_id, body=folder_metadata).execute()
                logger.info(f"Successfully moved folder {folder_id} to trash")

        except ValueError:
            raise  # Re-raise ValueError from validation
        except Exception as e:
            logger.error(f"Failed to delete folder {folder_id}: {type(e).__name__}: {e}")
            raise

    def upload_folder(
        self,
        local_path: str,
        parent_id: str | None = None,
        recursive: bool = True,
        workers: int | None = None,
    ) -> dict[str, Any]:
        """Upload a local folder to Google Drive with parallel file uploads.

        This method creates the folder structure and uploads files in parallel for
        improved performance. Requires additional imports: Path, ThreadPoolExecutor,
        as_completed, tqdm, sys, os, mimetypes.

        Args:
            local_path: Path to the local folder to upload
            parent_id: ID of the parent folder in Drive (None = My Drive root)
            recursive: If True, upload subdirectories recursively
            workers: Number of parallel upload workers (None = use os.cpu_count())

        Returns:
            Dictionary with folder metadata, lists of created items, and summary counts:
            {
                'folder': root folder metadata,
                'folders': list of created folders,
                'files': list of uploaded files,
                'total_files': count of files,
                'total_folders': count of folders,
                'total_bytes': total size in bytes
            }

        Raises:
            FileNotFoundError: If local_path does not exist or is not a directory
            Exception: If upload fails

        Examples:
            >>> client = DriveClient(credentials)
            >>> # Upload folder to My Drive root
            >>> result = client.upload_folder("/path/to/folder")
            >>> print(f"Created {len(result['folders'])} folders, "
            ...       f"{len(result['files'])} files")

            >>> # Upload to specific parent, non-recursive
            >>> result = client.upload_folder(
            ...     "/path/to/folder",
            ...     parent_id="1abc123",
            ...     recursive=False
            ... )

            >>> # Upload with custom worker count
            >>> result = client.upload_folder(
            ...     "/path/to/folder",
            ...     workers=8
            ... )
        """
        # This method requires additional imports that are added at module level
        import mimetypes
        import os
        import sys
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from pathlib import Path

        from tqdm import tqdm

        # Validate local path
        local_path_obj = Path(local_path).expanduser().resolve()
        if not local_path_obj.exists():
            error_msg = f"Path not found: {local_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        if not local_path_obj.is_dir():
            error_msg = f"Path is not a directory: {local_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        folder_name = local_path_obj.name
        logger.info(
            f"Uploading folder: {local_path} as '{folder_name}' to parent: {parent_id or 'root'}"
        )

        # Determine number of workers
        if workers is None:
            workers = os.cpu_count() or 4
        logger.debug(f"Using {workers} parallel upload workers")

        # Track created items
        created_folders: list[dict[str, Any]] = []
        created_files: list[dict[str, Any]] = []

        # Folder ID mapping: local path -> Drive folder ID
        folder_mapping: dict[str, str] = {}

        # Helper function to upload a single file
        def upload_single_file(file_path: Path, parent_drive_id: str) -> dict[str, Any] | None:
            """Upload a single file with error handling."""
            try:
                # Auto-detect MIME type
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    mime_type = "application/octet-stream"

                # Build file metadata
                file_metadata: dict[str, Any] = {
                    "name": file_path.name,
                    "parents": [parent_drive_id],
                }

                # Import MediaFileUpload here to avoid circular import issues
                from googleapiclient.http import MediaFileUpload

                # Create media upload
                media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

                # Upload file
                file: dict[str, Any] = (
                    self.service.files()
                    .create(
                        body=file_metadata,
                        media_body=media,
                        fields="id, name, mimeType, size",
                    )
                    .execute()
                )
                return file
            except Exception as e:
                logger.error(f"Failed to upload file {file_path.name}: {e}")
                return None

        try:
            # Create root folder
            root_folder = self.create_folder(folder_name, parent_id=parent_id)
            created_folders.append(root_folder)
            folder_mapping[str(local_path_obj)] = root_folder["id"]
            logger.info(f"Created root folder: {root_folder['name']} (ID: {root_folder['id']})")

            # Collect all items to upload
            folders_to_create: list[tuple[Path, str]] = []  # (local_path, parent_id)
            files_to_upload: list[tuple[Path, str]] = []  # (local_path, parent_id)

            # Walk directory tree
            if recursive:
                items = local_path_obj.rglob("*")
            else:
                items = local_path_obj.glob("*")

            for item in items:
                parent_local_path = item.parent

                # Get parent folder ID in Drive
                if str(parent_local_path) in folder_mapping:
                    parent_drive_id = folder_mapping[str(parent_local_path)]
                else:
                    parent_drive_id = root_folder["id"]

                if item.is_dir():
                    folders_to_create.append((item, parent_drive_id))
                elif item.is_file():
                    files_to_upload.append((item, parent_drive_id))

            # Create folders first (must be sequential for hierarchy)
            logger.info(f"Creating {len(folders_to_create)} folders...")
            for folder_path, parent_drive_id in tqdm(
                folders_to_create, desc="Creating folders", file=sys.stderr, disable=False
            ):
                try:
                    folder = self.create_folder(folder_path.name, parent_id=parent_drive_id)
                    created_folders.append(folder)
                    folder_mapping[str(folder_path)] = folder["id"]
                    logger.debug(f"Created folder: {folder_path.name} (ID: {folder['id']})")
                except Exception as e:
                    logger.error(f"Failed to create folder {folder_path.name}: {e}")
                    # Continue with other items

            # Upload files in parallel
            logger.info(f"Uploading {len(files_to_upload)} files with {workers} workers...")

            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all upload tasks
                future_to_file = {
                    executor.submit(upload_single_file, file_path, parent_drive_id): file_path
                    for file_path, parent_drive_id in files_to_upload
                }

                # Process completed uploads with progress bar
                with tqdm(
                    total=len(files_to_upload),
                    desc="Uploading files",
                    file=sys.stderr,
                    disable=False,
                ) as pbar:
                    for future in as_completed(future_to_file):
                        file_path = future_to_file[future]
                        try:
                            result = future.result()
                            if result:
                                created_files.append(result)
                                logger.debug(
                                    f"Uploaded file: {result['name']} (ID: {result['id']})"
                                )
                        except Exception as e:
                            logger.error(f"Upload failed for {file_path.name}: {e}")
                        finally:
                            pbar.update(1)

            # Calculate total bytes
            total_bytes = sum(int(f.get("size", 0)) for f in created_files)

            logger.info(
                f"Successfully uploaded folder: {len(created_folders)} folders, "
                f"{len(created_files)} files, {total_bytes} bytes"
            )

            return {
                "folder": root_folder,
                "folders": created_folders,
                "files": created_files,
                "total_files": len(created_files),
                "total_folders": len(created_folders),
                "total_bytes": total_bytes,
            }

        except Exception as e:
            logger.error(f"Failed to upload folder {local_path}: {type(e).__name__}: {e}")
            raise

    def upload_file(
        self,
        local_path: str,
        folder_id: str | None = None,
        name: str | None = None,
        mime_type: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Upload a file to Google Drive.

        Args:
            local_path: Path to the local file to upload
            folder_id: ID of the folder to upload to (None = My Drive root)
            name: Name for the file in Drive (None = use local filename)
            mime_type: MIME type of the file (None = auto-detect)
            description: Description for the file

        Returns:
            Dictionary with uploaded file metadata (id, name, mimeType, webViewLink, etc.)

        Raises:
            FileNotFoundError: If local_path does not exist
            ValueError: If file with same name already exists in target folder
            Exception: If upload fails

        Examples:
            >>> client = DriveClient(credentials)
            >>> # Upload to My Drive root
            >>> file = client.upload_file("/path/to/document.pdf")
            >>> print(f"Uploaded: {file['name']} (ID: {file['id']})")

            >>> # Upload to specific folder with custom name
            >>> file = client.upload_file(
            ...     "/path/to/report.pdf",
            ...     folder_id="1abc123",
            ...     name="Monthly Report.pdf",
            ...     description="January 2025 report"
            ... )
        """
        import mimetypes
        import os

        from googleapiclient.http import MediaFileUpload

        # Validate local path exists
        if not os.path.exists(local_path):
            logger.error(f"File not found: {local_path}")
            raise FileNotFoundError(f"File not found: {local_path}")

        # Determine filename
        file_name = name if name else os.path.basename(local_path)
        logger.info(
            f"Uploading file: {local_path} as '{file_name}' to folder: {folder_id or 'root'}"
        )

        # Auto-detect MIME type if not provided
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(local_path)
            if mime_type is None:
                mime_type = "application/octet-stream"
                logger.debug(f"Could not detect MIME type, using: {mime_type}")
            else:
                logger.debug(f"Auto-detected MIME type: {mime_type}")

        # Check if file with same name already exists in target folder
        escaped_name = file_name.replace("'", "\\'")
        query_parts = [f"name='{escaped_name}'", "trashed=false"]
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        else:
            query_parts.append("'root' in parents")

        check_query = " and ".join(query_parts)
        logger.debug(f"Checking for existing file with query: {check_query}")

        try:
            existing_files = self.list_files(query=check_query, max_results=1)
            if existing_files:
                error_msg = (
                    f"File with name '{file_name}' already exists in "
                    f"{'folder ' + folder_id if folder_id else 'My Drive root'}. "
                    f"Existing file ID: {existing_files[0]['id']}. "
                    f"Use rename_file() to rename the existing file first, "
                    f"or choose a different name."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        except ValueError:
            raise  # Re-raise ValueError from duplicate check
        except Exception as e:
            logger.warning(f"Could not check for existing files: {type(e).__name__}: {e}")

        # Build file metadata
        file_metadata: dict[str, Any] = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]
        if description:
            file_metadata["description"] = description

        try:
            # Create media upload
            media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

            # Upload file
            logger.debug(f"Starting upload: {file_name} ({mime_type})")
            file: dict[str, Any] = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, "
                    "webViewLink, iconLink, parents, description",
                )
                .execute()
            )

            logger.info(
                f"Successfully uploaded file: {file['name']} (ID: {file['id']}, "
                f"Size: {file.get('size', 'unknown')} bytes)"
            )
            return file

        except Exception as e:
            logger.error(f"Failed to upload file {local_path}: {type(e).__name__}: {e}")
            raise

    def rename_file(self, file_id: str, new_name: str) -> dict[str, Any]:
        """Rename a file in Google Drive.

        Args:
            file_id: The Drive file ID
            new_name: New name for the file

        Returns:
            Dictionary with updated file metadata

        Raises:
            Exception: If rename fails or file not found

        Examples:
            >>> client = DriveClient(credentials)
            >>> file = client.rename_file("1abc123xyz", "New Document Name.pdf")
            >>> print(f"Renamed to: {file['name']}")
        """
        logger.info(f"Renaming file {file_id} to '{new_name}'")

        try:
            # Update file metadata
            file_metadata = {"name": new_name}
            file: dict[str, Any] = (
                self.service.files()
                .update(
                    fileId=file_id,
                    body=file_metadata,
                    fields="id, name, mimeType, size, modifiedTime, webViewLink, parents",
                )
                .execute()
            )

            logger.info(f"Successfully renamed file {file_id} to '{file['name']}'")
            return file

        except Exception as e:
            logger.error(f"Failed to rename file {file_id}: {type(e).__name__}: {e}")
            raise

    def move_file(self, file_id: str, destination_folder_id: str) -> dict[str, Any]:
        """Move a file to a different folder in Google Drive.

        Args:
            file_id: The Drive file ID
            destination_folder_id: ID of the destination folder

        Returns:
            Dictionary with updated file metadata

        Raises:
            Exception: If move fails or file/folder not found

        Examples:
            >>> client = DriveClient(credentials)
            >>> file = client.move_file("1abc123xyz", "1folder456")
            >>> print(f"Moved {file['name']} to new folder")
        """
        logger.info(f"Moving file {file_id} to folder {destination_folder_id}")

        try:
            # Get current parents
            file = self.service.files().get(fileId=file_id, fields="parents, name").execute()
            previous_parents = ",".join(file.get("parents", []))
            file_name = file.get("name", "unknown")

            logger.debug(
                f"Moving file '{file_name}' from parents [{previous_parents}] "
                f"to [{destination_folder_id}]"
            )

            # Move file by adding new parent and removing old parents
            updated_file: dict[str, Any] = (
                self.service.files()
                .update(
                    fileId=file_id,
                    addParents=destination_folder_id,
                    removeParents=previous_parents,
                    fields="id, name, mimeType, size, modifiedTime, webViewLink, parents",
                )
                .execute()
            )

            logger.info(
                f"Successfully moved file '{file_name}' (ID: {file_id}) "
                f"to folder {destination_folder_id}"
            )
            return updated_file

        except Exception as e:
            logger.error(f"Failed to move file {file_id}: {type(e).__name__}: {e}")
            raise

    def delete_file(self, file_id: str, permanent: bool = False) -> None:
        """Delete a file in Google Drive.

        Args:
            file_id: The Drive file ID
            permanent: If False (default), move to trash. If True, permanently delete.

        Raises:
            Exception: If delete fails or file not found

        Examples:
            >>> client = DriveClient(credentials)
            >>> # Move to trash (recoverable)
            >>> client.delete_file("1abc123xyz")

            >>> # Permanently delete (irreversible)
            >>> client.delete_file("1abc123xyz", permanent=True)
        """
        action = "Permanently deleting" if permanent else "Trashing"
        logger.info(f"{action} file {file_id}")

        try:
            if permanent:
                # Permanently delete
                self.service.files().delete(fileId=file_id).execute()
                logger.info(f"Successfully permanently deleted file {file_id}")
            else:
                # Move to trash
                file_metadata = {"trashed": True}
                self.service.files().update(fileId=file_id, body=file_metadata).execute()
                logger.info(f"Successfully moved file {file_id} to trash")

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {type(e).__name__}: {e}")
            raise
