import os
import tempfile
import re
from pathlib import Path
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

    @patch.object(requests.Session, 'request')
    def test_request_success(self, mock_request):
        """Test successful request with no token refresh needed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        session = TokenRefreshSession(
            "https://api.example.com", "test_api_key")
        response = session.request(
            "GET", "https://api.example.com/some/endpoint")

        assert response == mock_response
        mock_request.assert_called_once_with(
            "GET", "https://api.example.com/some/endpoint")

    @patch.object(requests.Session, 'request')
    @patch.object(TokenRefreshSession, '_refresh_token')
    def test_request_with_token_refresh(self, mock_refresh_token, mock_request):
        """Test request that initially fails with 401 but succeeds after token refresh."""
        # First response is 401, second response (after token refresh) is 200
        mock_401_response = Mock()
        mock_401_response.status_code = 401

        mock_200_response = Mock()
        mock_200_response.status_code = 200

        mock_request.side_effect = [mock_401_response, mock_200_response]
        mock_refresh_token.return_value = True

        session = TokenRefreshSession(
            "https://api.example.com", "test_api_key")
        response = session.request(
            "GET", "https://api.example.com/some/endpoint")

        assert response == mock_200_response
        assert mock_request.call_count == 2
        mock_refresh_token.assert_called_once()

    @patch.object(requests.Session, 'request')
    @patch.object(TokenRefreshSession, '_refresh_token')
    def test_request_with_failed_token_refresh(self, mock_refresh_token, mock_request):
        """Test request that fails with 401 and token refresh also fails."""
        mock_401_response = Mock()
        mock_401_response.status_code = 401

        mock_request.return_value = mock_401_response
        mock_refresh_token.return_value = False

        session = TokenRefreshSession(
            "https://api.example.com", "test_api_key")

        with pytest.raises(Exception, match="Token refresh failed"):
            session.request("GET", "https://api.example.com/some/endpoint")

        mock_request.assert_called_once()
        mock_refresh_token.assert_called_once()

    @patch.object(requests.Session, 'get')
    def test_refresh_token_success(self, mock_get):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"new_access_token": "new_token"}
        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        session = TokenRefreshSession(
            "https://api.example.com", "test_api_key")
        result = session._refresh_token()

        assert result is True
        assert session.headers["x-openrelik-access-token"] == "new_token"
        mock_get.assert_called_once_with(
            "https://api.example.com/auth/refresh")
        mock_response.raise_for_status.assert_called_once()

    @patch.object(requests.Session, 'get')
    def test_refresh_token_failure(self, mock_get):
        """Test failed token refresh."""
        mock_get.side_effect = RequestException("Connection error")

        session = TokenRefreshSession(
            "https://api.example.com", "test_api_key")
        result = session._refresh_token()

        assert result is False
        mock_get.assert_called_once_with(
            "https://api.example.com/auth/refresh")


class TestAPIClient:
    def test_init(self):
        """Test APIClient initialization."""
        api_server_url = "https://api.example.com"
        api_key = "test_api_key"
        api_version = "v2"

        with patch('openrelik_api_client.api_client.TokenRefreshSession') as mock_session_class:
            client = APIClient(api_server_url, api_key, api_version)

            assert client.base_url == f"{api_server_url}/api/{api_version}"
            mock_session_class.assert_called_once_with(api_server_url, api_key)
            assert client.session == mock_session_class.return_value

    def test_init_default_version(self):
        """Test APIClient initialization with default API version."""
        api_server_url = "https://api.example.com"
        api_key = "test_api_key"

        with patch('openrelik_api_client.api_client.TokenRefreshSession') as mock_session_class:
            client = APIClient(api_server_url, api_key)

            assert client.base_url == f"{api_server_url}/api/v1"

    def test_get(self):
        """Test GET request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.get("/endpoint", params={"param": "value"})

        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            params={"param": "value"}
        )

    def test_post(self):
        """Test POST request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.post("/endpoint", data={"key": "value"},
                    json={"json_key": "json_value"})

        client.session.post.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            data={"key": "value"},
            json={"json_key": "json_value"}
        )

    def test_put(self):
        """Test PUT request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.put("/endpoint", data={"key": "value"})

        client.session.put.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            data={"key": "value"}
        )

    def test_patch(self):
        """Test PATCH request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.patch(
            "/endpoint", data={"key": "value"}, json={"json_key": "json_value"})

        client.session.patch.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            data={"key": "value"},
            json={"json_key": "json_value"}
        )

    def test_delete(self):
        """Test DELETE request method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        client.delete("/endpoint", params={"param": "value"})

        client.session.delete.assert_called_once_with(
            "https://api.example.com/api/v1/endpoint",
            params={"param": "value"}
        )

    def test_get_config(self):
        """Test get_config method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"config": "value"}
        client.session.get.return_value = mock_response

        config = client.get_config()

        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/config/system/")
        mock_response.raise_for_status.assert_called_once()
        assert config == {"config": "value"}

    @patch('tempfile.NamedTemporaryFile')
    def test_download_file(self, mock_temp_file):
        """Test download_file method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.raise_for_status = MagicMock()  # Ensure raise_for_status is mocked
        client.session.get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.name = "/tmp/test_file.txt"
        # The SUT calls NamedTemporaryFile directly, not as a context manager.
        mock_temp_file.return_value = mock_file

        result = client.download_file(123, "test_file.txt")

        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/files/123/download")
        mock_response.raise_for_status.assert_called_once()
        mock_file.write.assert_called_once_with(b"file content")
        assert result == "/tmp/test_file.txt"

    @patch('os.path.splitext')
    @patch('tempfile.NamedTemporaryFile')
    def test_download_file_with_extension(self, mock_temp_file, mock_splitext):
        """Test download_file method with file extension handling."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        mock_response = MagicMock()
        mock_response.content = b"file content"
        # Ensure raise_for_status is mocked as it's called in the SUT
        mock_response.raise_for_status = MagicMock()
        client.session.get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.name = "/tmp/test_file.txt"
        mock_temp_file.return_value = mock_file # Correct for direct instantiation

        mock_splitext.return_value = ("test_file", ".txt")

        result = client.download_file(123, "test_file.txt")

        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/files/123/download")
        mock_splitext.assert_called_once_with("test_file.txt")
        mock_response.raise_for_status.assert_called_once()
        mock_temp_file.assert_called_once_with(
            mode="wb",
            prefix="test_file",
            suffix=".txt",
            delete=False
        )
        mock_file.write.assert_called_once_with(b"file content")
        assert result == "/tmp/test_file.txt"

    @patch('openrelik_api_client.api_client.Path')
    @patch('openrelik_api_client.api_client.uuid4')
    @patch('openrelik_api_client.api_client.MultipartEncoder')
    def test_upload_file_success(self, mock_multipart_encoder, mock_uuid4, mock_path):
        """Test successful upload_file method."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        # Mock Path
        mock_file_path = MagicMock()
        mock_file_path.name = "test_file.txt"
        mock_file_path.exists.return_value = True
        mock_path.return_value = mock_file_path

        # Mock file stat
        mock_stat = MagicMock()
        mock_stat.st_size = 15 * 1024 * 1024  # 15 MB
        mock_file_path.stat.return_value = mock_stat

        # Mock UUID
        mock_uuid4.return_value.hex = "mock-uuid"

        # Mock responses
        mock_folder_response = MagicMock()
        mock_folder_response.status_code = 200

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 201
        mock_upload_response.json.return_value = {"id": 456}

        client.session.get.return_value = mock_folder_response
        client.session.post.return_value = mock_upload_response

        # Mock file open
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.side_effect = [
            b"chunk1", b"chunk2", b""]

        with patch('builtins.open', return_value=mock_file):
            result = client.upload_file("test_file.txt", 789)

        assert result == 456
        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/folders/789")
        assert client.session.post.call_count == 2  # Two chunks

    @patch('openrelik_api_client.api_client.Path')
    def test_upload_file_file_not_found(self, mock_path_constructor):
        """Test upload_file method with non-existent file."""
        client = APIClient("https://api.example.com")

        file_path_str = "nonexistent_file.txt"

        mock_path_object = MagicMock(spec=Path)
        mock_path_object.exists.return_value = False
        mock_path_object.__str__.return_value = file_path_str  # Control string representation
        mock_path_constructor.return_value = mock_path_object

        expected_error_message = f"File {file_path_str} not found."
        with pytest.raises(FileNotFoundError, match=re.escape(expected_error_message)):
            client.upload_file(file_path_str, 789)

        mock_path_constructor.assert_called_once_with(file_path_str)

    @patch('openrelik_api_client.api_client.Path')
    def test_upload_file_folder_not_found(self, mock_path):
        """Test upload_file method with non-existent folder."""
        client = APIClient("https://api.example.com")
        client.session = MagicMock()

        mock_file_path = MagicMock()
        mock_file_path.name = "test_file.txt"
        mock_file_path.exists.return_value = True
        mock_path.return_value = mock_file_path

        mock_folder_response = MagicMock()
        mock_folder_response.status_code = 404
        client.session.get.return_value = mock_folder_response

        result = client.upload_file("test_file.txt", 999)

        assert result is None
        client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/folders/999")
