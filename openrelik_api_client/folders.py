# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any

from openrelik_api_client.api_client import APIClient


class FoldersAPI:
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client

    def list_root_folders(
        self, limit: int, pagination_metadata: bool = False
    ) -> list[dict[str, Any]]:
        """List root folders.

        Args:
            limit: Maximum number of folders to return.
            pagination_metadata: If True, include pagination metadata in the response.

        Returns:
            A list of dictionaries containing folder metadata.

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.api_client.base_url}/folders/all/?page_size={limit}"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        if pagination_metadata:
            folders = response.json()
        else:
            folders = response.json().get("folders", [])
        return folders

    def list_folder(self, folder_id: int) -> list[dict[str, Any]]:
        """List files in a folder.

        Args:
            folder_id: The ID of the folder to check.

        Returns:
            A list of dictionaries containing file metadata

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.api_client.base_url}/folders/{folder_id}/files/"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        return response.json()

    def create_root_folder(self, display_name: str) -> int | None:
        """Create a root folder.

        Args:
            display_name (str): Folder display name.

        Returns:
            int: Folder ID for the new root folder, or None otherwise.

        Raises:
            HTTPError: If the API request failed.
        """
        folder_id = None
        endpoint = f"{self.api_client.base_url}/folders/"
        params = {"display_name": display_name}
        response = self.api_client.session.post(endpoint, json=params)
        response.raise_for_status()
        if response.status_code == 201:
            folder_id = response.json().get("id")
        return folder_id

    def create_subfolder(self, folder_id: int, display_name: str) -> int | None:
        """Create a subfolder within the given folder ID.

        Args:
            folder_id: The ID of the parent folder.
            display_name: The name of the subfolder to check.

        Returns:
            int: Folder ID for the new root folder, or None.

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.api_client.base_url}/folders/{folder_id}/folders/"
        data = {"display_name": display_name}
        response = self.api_client.session.post(endpoint, json=data)
        response.raise_for_status()

        new_folder_id = None
        if response.status_code == 201:
            new_folder_id = response.json().get("id")
        return new_folder_id

    def folder_exists(self, folder_id: int) -> bool:
        """Checks if a folder with the given ID exists.

        Args:
            folder_id: The ID of the folder to check.

        Returns:
            True if the folder exists, False otherwise.

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.api_client.base_url}/folders/{folder_id}"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        return response.status_code == 200

    def update_folder(self, folder_id: int, folder_data: dict[str, Any]) -> dict[str, Any] | None:
        """Updates an existing folder.

        Args:
            folder_id: The ID of the folder to update.
            folder_data: The updated folder data.

        Returns:
            The updated folder data, or None.

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.api_client.base_url}/folders/{folder_id}"
        response = self.api_client.session.patch(endpoint, json=folder_data)
        response.raise_for_status()
        return response.json()

    def delete_folder(self, folder_id: int) -> bool:
        """Deletes an existing folder.

        Args:
            folder_id: The ID of the folder to update.

        Returns:
            True if the request was successful.

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.api_client.base_url}/folders/{folder_id}"
        response = self.api_client.session.delete(endpoint)
        response.raise_for_status()
        return response.status_code == 204

    def share_folder(
        self,
        folder_id: int,
        user_names: list[str] | None = None,
        group_names: list[str] | None = None,
        user_ids: list[int] | None = None,
        group_ids: list[int] | None = None,
        user_role: str | None = None,
        group_role: str | None = None,
    ) -> dict[str, Any] | None:
        """Shares a folder with specified users and/or groups.

        The server expects all fields in the FolderShareRequest schema to be present.
        If user_role or group_role are not provided, they default to "viewer".

        Args:
            folder_id: The ID of the folder to share.
            user_names: A list of usernames to share the folder with.
            group_names: A list of group names to share the folder with.
            user_ids: A list of user IDs to share the folder with.
            group_ids: A list of group IDs to share the folder with.
            user_role: The role to assign to the specified users (e.g., "viewer", "editor").
                       Defaults to "viewer" if not provided.
            group_role: The role to assign to the specified groups (e.g., "viewer", "editor").
                        Defaults to "viewer" if not provided.

        Returns:
            None if the sharing operation was successful. The server returns a null body
            which is deserialized to None.

        Raises:
            requests.exceptions.HTTPError: If the API request failed (e.g., folder not found,
                                           invalid role, permission denied).
        """
        endpoint = f"{self.api_client.base_url}/folders/{folder_id}/roles"

        # Ensure lists are not None for the payload
        payload_user_ids = user_ids if user_ids is not None else []
        payload_user_names = user_names if user_names is not None else []
        payload_group_ids = group_ids if group_ids is not None else []
        payload_group_names = group_names if group_names is not None else []

        # Default roles to "viewer" if not provided, as the server schema requires these fields.
        payload_user_role = user_role if user_role is not None else "viewer"
        payload_group_role = group_role if group_role is not None else "viewer"

        data = {
            "user_ids": payload_user_ids,
            "user_names": payload_user_names,
            "group_ids": payload_group_ids,
            "group_names": payload_group_names,
            "user_role": payload_user_role,
            "group_role": payload_group_role,
        }
        try:
            response = self.api_client.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"An error occurred: {e.response.json()}")
            return None
