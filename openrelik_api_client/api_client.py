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

import warnings
from typing import Any

import requests
from requests.exceptions import RequestException

from .configs import ConfigsAPI
from .files import FilesAPI


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
        """
        DEPRECATED: Use configAPI.get_system_config() instead.
        This method will be removed in a future version.
        """
        warnings.warn(
            "The 'APIClient.get_config' method is deprecated. Please use 'configAPI.get_system_config()' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        configs_api = ConfigsAPI(self)
        return configs_api.get_system_config()

    def download_file(self, file_id: int, filename: str) -> str | None:
        """
        DEPRECATED: Use filesAPI.download_file() instead.
        This method will be removed in a future version.
        """
        warnings.warn(
            "The 'APIClient.download_file' method is deprecated. Please use 'filesAPI.download_file()' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        files_api = FilesAPI(self)
        return files_api.download_file(file_id, filename)

    def upload_file(self, file_path: str, folder_id: int) -> int | None:
        """
        DEPRECATED: Use filesAPI.download_file() instead.
        This method will be removed in a future version.
        """
        warnings.warn(
            "The 'APIClient.upload_file' method is deprecated. Please use 'filesAPI.upload_file()' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        files_api = FilesAPI(self)
        return files_api.upload_file(file_path, folder_id)


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
            if self._refresh_token(url):
                # Retry the original request with the new token
                response = super().request(method, url, **kwargs)
            else:
                raise RuntimeError("API key has expired")

        return response

    def _refresh_token(self, requested_url: str) -> bool:
        """Refreshes the access token using the refresh token."""
        refresh_url = f"{self.api_server_url}/auth/refresh"

        # If the original URL is the same as the refresh URL, do not attempt to refresh as this
        # indicates a faulty or expired api key. This prevents an infinite loop of refresh attempts.
        if requested_url == refresh_url:
            return False

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
