# Copyright 2025 Google LLC
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

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests.exceptions import RequestException

from openrelik_api_client.api_client import APIClient, TokenRefreshSession


class TestTokenRefreshSession:
    def test_init(self):
        """Test TokenRefreshSession initialization."""
        api_server_url = "https://api.example.com"
        api_key = "test_api_key"
        session = TokenRefreshSession(api_server_url, api_key)

        assert session.api_server_url == api_server_url
        assert session.headers["x-openrelik-refresh-token"] == api_key

    def test_init_without_api_key(self):
        """Test TokenRefreshSession initialization without API key."""
        api_server_url = "https://api.example.com"
        session = TokenRefreshSession(api_server_url, None)

        assert session.api_server_url == api_server_url
        assert "x-openrelik-refresh-token" not in session.headers

    @patch.object(requests.Session, "request")
    def test_request_success(self, mock_request):
        """Test successful request with no token refresh needed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        session = TokenRefreshSession("https://api.example.com", "test_api_key")
        response = session.request("GET", "https://api.example.com/some/endpoint")

        assert response == mock_response
        mock_request.assert_called_once_with("GET", "https://api.example.com/some/endpoint")

    @patch.object(requests.Session, "request")
    @patch.object(TokenRefreshSession, "_refresh_token")
    def test_request_with_token_refresh(self, mock_refresh_token, mock_request):
        """Test request that initially fails with 401 but succeeds after token refresh."""
        # First response is 401, second response (after token refresh) is 200
        mock_401_response = Mock()
        mock_401_response.status_code = 401

        mock_200_response = Mock()
        mock_200_response.status_code = 200

        mock_request.side_effect = [mock_401_response, mock_200_response]
        mock_refresh_token.return_value = True

        session = TokenRefreshSession("https://api.example.com", "test_api_key")
        response = session.request("GET", "https://api.example.com/some/endpoint")

        assert response == mock_200_response
        assert mock_request.call_count == 2
        mock_refresh_token.assert_called_once()

    @patch.object(requests.Session, "request")
    @patch.object(TokenRefreshSession, "_refresh_token")
    def test_request_with_failed_token_refresh(self, mock_refresh_token, mock_request):
        """Test request that fails with 401 and token refresh also fails."""
        mock_401_response = Mock()
        mock_401_response.status_code = 401

        mock_request.return_value = mock_401_response
        mock_refresh_token.return_value = False

        session = TokenRefreshSession("https://api.example.com", "test_api_key")

        with pytest.raises(Exception, match="Token refresh failed"):
            session.request("GET", "https://api.example.com/some/endpoint")

        mock_request.assert_called_once()
        mock_refresh_token.assert_called_once()

    @patch.object(requests.Session, "get")
    def test_refresh_token_success(self, mock_get):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"new_access_token": "new_token"}
        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        session = TokenRefreshSession("https://api.example.com", "test_api_key")
        result = session._refresh_token()

        assert result is True
        assert session.headers["x-openrelik-access-token"] == "new_token"
        mock_get.assert_called_once_with("https://api.example.com/auth/refresh")
        mock_response.raise_for_status.assert_called_once()

    @patch.object(requests.Session, "get")
    def test_refresh_token_failure(self, mock_get):
        """Test failed token refresh."""
        mock_get.side_effect = RequestException("Connection error")

        session = TokenRefreshSession("https://api.example.com", "test_api_key")
        result = session._refresh_token()

        assert result is False
        mock_get.assert_called_once_with("https://api.example.com/auth/refresh")


class TestAPIClient:
    def test_init(self):
        """Test APIClient initialization."""
        api_server_url = "https://api.example.com"
        api_key = "test_api_key"
        api_version = "v2"

        with patch("openrelik_api_client.api_client.TokenRefreshSession") as mock_session_class:
            client = APIClient(api_server_url, api_key, api_version)

            assert client.base_url == f"{api_server_url}/api/{api_version}"
            mock_session_class.assert_called_once_with(api_server_url, api_key)
            assert client.session == mock_session_class.return_value

    def test_init_default_version(self):
        """Test APIClient initialization with default API version."""
        api_server_url = "https://api.example.com"
        api_key = "test_api_key"

        with patch("openrelik_api_client.api_client.TokenRefreshSession") as mock_session_class:
            client = APIClient(api_server_url, api_key)

            assert client.base_url == f"{api_server_url}/api/v1"

    def test_get(self):
        """Test GET request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.get("/endpoint", params={"param": "value"})

        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint", params={"param": "value"}
        )

    def test_post(self):
        """Test POST request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.post("/endpoint", data={"key": "value"}, json={"json_key": "json_value"})

        client.session.post.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            data={"key": "value"},
            json={"json_key": "json_value"},
        )

    def test_put(self):
        """Test PUT request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.put("/endpoint", data={"key": "value"})

        client.session.put.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint", data={"key": "value"}
        )

    def test_patch(self):
        """Test PATCH request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.patch("/endpoint", data={"key": "value"}, json={"json_key": "json_value"})

        client.session.patch.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            data={"key": "value"},
            json={"json_key": "json_value"},
        )

    def test_delete(self):
        """Test DELETE request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.delete("/endpoint", params={"param": "value"})

        client.session.delete.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint", params={"param": "value"}
        )
