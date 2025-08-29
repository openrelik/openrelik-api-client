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

import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from requests.exceptions import RequestException
from requests_toolbelt import MultipartEncoder


class APIClient:
    """
    A reusable API client that automatically handles token refresh on 401 responses.

    Attributes:
        api_server_url (str): The URL of the API server.
        api_key (str): The API key.
        api_version (str): The API version.
        session (requests.Session): The session object.

    Example usage:
        client = APIClient(api_server_url, refresh_token)
        response = client.get("/users/me/")
        print(response.json())
    """

    def __init__(
        self,
        api_server_url,
        api_key=None,
        api_version="v1",
    ):
        self.base_url = f"{api_server_url}/api/{api_version}"
        self.session = TokenRefreshSession(api_server_url, api_key)

    def get(self, endpoint, **kwargs):
        """Sends a GET request to the specified API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, **kwargs)

    def post(self, endpoint, data=None, json=None, **kwargs):
        """Sends a POST request to the specified API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, data=data, json=json, **kwargs)

    def put(self, endpoint, data=None, **kwargs):
        """Sends a PUT request to the specified API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, data=data, **kwargs)

    def patch(self, endpoint, data=None, json=None, **kwargs):
        """Sends a PATCH request to the specified API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.patch(url, data=data, json=json, **kwargs)

    def delete(self, endpoint, **kwargs):
        """Sends a DELETE request to the specified API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, **kwargs)

    def get_config(self) -> dict[str, Any]:
        """Gets the current OpenRelik configuration."""
        endpoint = f"{self.base_url}/config/system/"
        response = self.session.get(endpoint)
        response.raise_for_status()
        return response.json()

    def download_file(self, file_id: int, filename: str) -> str | None:
        """Downloads a file from OpenRelik.

        Args:
            file_id: The ID of the file to download.
            filename: The name of the file to download.

        Returns:
            str: The path to the downloaded file.
        """
        endpoint = f"{self.base_url}/files/{file_id}/download"
        response = self.session.get(endpoint)
        response.raise_for_status()
        filename_prefix, extension = os.path.splitext(filename)
        file = tempfile.NamedTemporaryFile(
            mode="wb", prefix=f"{filename_prefix}", suffix=extension, delete=False
        )
        file.write(response.content)
        file.close()
        return file.name

    def upload_file(self, file_path: str, folder_id: int) -> int | None:
        """Uploads a file to the server.

        Args:
            file_path: File contents.
            folder_id: An existing OpenRelik folder identifier.

        Returns:
            file_id of the uploaded file or None otherwise.

        Raise:
            FileNotFoundError: if file_path is not found.
        """
        MAX_CHUNK_RETRIES = 10  # Maximum number of retries for chunk upload
        CHUNK_RETRY_INTERVAL = 0.5  # seconds

        file_id = None
        response = None
        endpoint = "/files/upload"
        chunk_size = 10 * 1024 * 1024  # 10 MB
        resumableTotalChunks = 0
        resumableChunkNumber = 0
        resumableIdentifier = uuid4().hex
        file_path = Path(file_path)
        resumableFilename = file_path.name
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")

        if folder_id:
            response = self.session.get(f"{self.base_url}/folders/{folder_id}")
            if response.status_code == 404:
                return file_id

        with open(file_path, "rb") as fh:
            total_size = Path(file_path).stat().st_size
            resumableTotalChunks = math.ceil(total_size / chunk_size)
            while chunk := fh.read(chunk_size):
                resumableChunkNumber += 1
                retry_count = 0
                while retry_count < MAX_CHUNK_RETRIES:
                    params = {
                        "resumableRelativePath": resumableFilename,
                        "resumableTotalSize": total_size,
                        "resumableCurrentChunkSize": len(chunk),
                        "resumableChunkSize": chunk_size,
                        "resumableChunkNumber": resumableChunkNumber,
                        "resumableTotalChunks": resumableTotalChunks,
                        "resumableIdentifier": resumableIdentifier,
                        "resumableFilename": resumableFilename,
                        "folder_id": folder_id,
                    }
                    encoder = MultipartEncoder(
                        {"file": (file_path.name, chunk, "application/octet-stream")}
                    )
                    headers = {"Content-Type": encoder.content_type}
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        data=encoder.to_string(),
                        params=params,
                    )
                    if response.status_code == 200 or response.status_code == 201:
                        # Success, move to the next chunk
                        break
                    elif response.status_code == 503:
                        # Server has issue saving the chunk, retry the upload.
                        retry_count += 1
                        time.sleep(CHUNK_RETRY_INTERVAL)
                    elif response.status_code == 429:
                        # Rate limit exceeded, cancel the upload and raise an error.
                        raise RuntimeError("Upload failed, maximum retries exceeded")
                    else:
                        # Other errors, cancel the upload and raise an error.
                        raise RuntimeError("Upload failed")

            if response and response.status_code == 201:
                file_id = response.json().get("id")

        return file_id


class TokenRefreshSession(requests.Session):
    """Custom session class that handles automatic token refresh on 401 responses."""

    def __init__(self, api_server_url, api_key):
        """
        Initializes the TokenRefreshSession with the API server URL and refresh token.

        Args:
            api_server_url (str): The URL of the API server.
            refresh_token (str): The refresh token.
        """
        super().__init__()
        self.api_server_url = api_server_url
        if api_key:
            self.headers["x-openrelik-refresh-token"] = api_key

    def request(self, method: str, url: str, **kwargs: dict[str, Any]) -> requests.Response:
        """Intercepts the request to handle token expiration.

        Args:
            method (str): The HTTP method.
            url (str): The URL of the request.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            Response: The response object.

        Raises:
            Exception: If the token refresh fails.
        """
        response = super().request(method, url, **kwargs)

        if response.status_code == 401:
            if self._refresh_token():
                # Retry the original request with the new token
                response = super().request(method, url, **kwargs)
            else:
                raise Exception("Token refresh failed")

        return response

    def _refresh_token(self) -> bool:
        """Refreshes the access token using the refresh token."""
        refresh_url = f"{self.api_server_url}/auth/refresh"
        try:
            response = self.get(refresh_url)
            response.raise_for_status()
            # Update session headers with the new access token
            new_access_token = response.json().get("new_access_token")
            self.headers["x-openrelik-access-token"] = new_access_token
            return True
        except RequestException as e:
            print(f"Failed to refresh token: {e}")
            return False
