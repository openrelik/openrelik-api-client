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

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openrelik_api_client.api_client import APIClient, TokenRefreshSession
from openrelik_api_client.files import FilesAPI


class TestAPIClient:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = MagicMock(spec=APIClient)
        self.api_client.session = MagicMock(spec=TokenRefreshSession)
        self.api_client.base_url = "https://api.example.com/api/v1"
        self.files_api = FilesAPI(self.api_client)

    def test_init(self):
        """Test FoldersAPI initialization."""
        assert self.files_api.api_client == self.api_client

    @patch("tempfile.NamedTemporaryFile")
    def test_download_file(self, mock_temp_file):
        """Test download_file method."""
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_response.raise_for_status = MagicMock()  # Ensure raise_for_status is mocked
        self.files_api.api_client.session.get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.name = "/tmp/test_file.txt"
        # The SUT calls NamedTemporaryFile directly, not as a context manager.
        mock_temp_file.return_value = mock_file

        result = self.files_api.download_file(123, "test_file.txt")

        self.files_api.api_client.session.get.assert_called_once_with(
            f"{self.api_client.base_url}/files/123/download"
        )
        mock_response.raise_for_status.assert_called_once()
        mock_file.write.assert_called_once_with(b"file content")
        assert result == "/tmp/test_file.txt"

    @patch("os.path.splitext")
    @patch("tempfile.NamedTemporaryFile")
    def test_download_file_with_extension(self, mock_temp_file, mock_splitext):
        """Test download_file method with file extension handling."""
        mock_response = MagicMock()
        mock_response.content = b"file content"
        # Ensure raise_for_status is mocked as it's called in the SUT
        mock_response.raise_for_status = MagicMock()
        self.files_api.api_client.session.get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.name = "/tmp/test_file.txt"
        mock_temp_file.return_value = mock_file  # Correct for direct instantiation

        mock_splitext.return_value = ("test_file", ".txt")

        result = self.files_api.download_file(123, "test_file.txt")

        self.files_api.api_client.session.get.assert_called_once_with(
            f"{self.api_client.base_url}/files/123/download"
        )
        mock_splitext.assert_called_once_with("test_file.txt")
        mock_response.raise_for_status.assert_called_once()
        mock_temp_file.assert_called_once_with(
            mode="wb", prefix="test_file", suffix=".txt", delete=False, dir=None
        )
        mock_file.write.assert_called_once_with(b"file content")
        assert result == "/tmp/test_file.txt"

    @patch("openrelik_api_client.files.Path")
    @patch("openrelik_api_client.files.uuid4")
    @patch("openrelik_api_client.files.MultipartEncoder")
    def test_upload_file_success(self, mock_multipart_encoder, mock_uuid4, mock_path):
        """Test successful upload_file method."""
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

        self.files_api.api_client.session.get.return_value = mock_folder_response
        self.files_api.api_client.session.post.return_value = mock_upload_response

        # Mock file open
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.side_effect = [b"chunk1", b"chunk2", b""]

        with patch("builtins.open", return_value=mock_file):
            result = self.files_api.upload_file("test_file.txt", 789)

        assert result == 456
        self.files_api.api_client.session.get.assert_called_once_with(
            f"{self.api_client.base_url}/folders/789"
        )
        assert self.files_api.api_client.session.post.call_count == 2  # Two chunks

    @patch("openrelik_api_client.files.Path")
    def test_upload_file_file_not_found(self, mock_path_constructor):
        """Test upload_file method with non-existent file."""
        file_path_str = "nonexistent_file.txt"

        mock_path_object = MagicMock(spec=Path)
        mock_path_object.exists.return_value = False
        mock_path_object.__str__.return_value = file_path_str  # Control string representation
        mock_path_constructor.return_value = mock_path_object

        expected_error_message = f"File {file_path_str} not found."
        with pytest.raises(FileNotFoundError, match=re.escape(expected_error_message)):
            self.files_api.upload_file(file_path_str, 789)

        mock_path_constructor.assert_called_once_with(file_path_str)

    @patch("openrelik_api_client.files.Path")
    def test_upload_file_folder_not_found(self, mock_path):
        """Test upload_file method with non-existent folder."""
        mock_file_path = MagicMock()
        mock_file_path.name = "test_file.txt"
        mock_file_path.exists.return_value = True
        mock_path.return_value = mock_file_path

        mock_folder_response = MagicMock()
        mock_folder_response.status_code = 404
        self.files_api.api_client.session.get.return_value = mock_folder_response

        result = self.files_api.upload_file("test_file.txt", 999)

        assert result is None
        self.files_api.api_client.session.get.assert_called_once_with(
            f"{self.api_client.base_url}/folders/999"
        )

    def test_get_file_metadata(self):
        """Test get_file_metadata method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "display_name": "test_file.txt",
            "filesize": 12345,
            "extension": ".txt",
            "original_path": "/path/to/test_file.txt",
            "magic_mime": "text/plain",
            "hash_md5": "d41d8cd98f00b204e9800998ecf8427e",
        }
        self.files_api.api_client.session.get.return_value = mock_response
        result = self.files_api.get_file_metadata(123)

        assert result == {
            "display_name": "test_file.txt",
            "filesize": 12345,
            "extension": ".txt",
            "original_path": "/path/to/test_file.txt",
            "magic_mime": "text/plain",
            "hash_md5": "d41d8cd98f00b204e9800998ecf8427e",
        }

        self.files_api.api_client.session.get.assert_called_once_with(
            f"{self.api_client.base_url}/files/123/"
        )

    def test_get_file_content_success(self):
        """Test get_file_content method for successful content retrieval."""
        mock_metadata_response = MagicMock()
        mock_metadata_response.json.return_value = {"filesize": 1024}
        mock_content_response = MagicMock()
        mock_content_response.content = b"file content"
        mock_content_response.raise_for_status = MagicMock()
        self.files_api.api_client.session.get.side_effect = [
            mock_metadata_response,
            mock_content_response,
        ]
        result = self.files_api.get_file_content(123, max_file_size_bytes=2048, return_type="bytes")
        assert result == b"file content"
        assert self.files_api.api_client.session.get.call_count == 2
        self.files_api.api_client.session.get.assert_any_call(
            f"{self.api_client.base_url}/files/123/download_stream"
        )
        mock_content_response.raise_for_status.assert_called_once()

    def test_get_file_content_too_large(self):
        """Test get_file_content method when file is too large."""
        mock_metadata_response = MagicMock()
        mock_metadata_response.json.return_value = {"filesize": 10 * 1024 * 1024}
        self.files_api.api_client.session.get.return_value = mock_metadata_response
        with pytest.raises(RuntimeError, match="File too large to download"):
            self.files_api.get_file_content(
                123, max_file_size_bytes=5 * 1024 * 1024, return_type="bytes"
            )

    def test_get_file_content_invalid_return_type(self):
        """Test get_file_content method with invalid return_type."""
        mock_metadata_response = MagicMock()
        mock_metadata_response.json.return_value = {"filesize": 1024}
        mock_content_response = MagicMock()
        mock_content_response.content = b"file content"
        mock_content_response.raise_for_status = MagicMock()
        self.files_api.api_client.session.get.side_effect = [
            mock_metadata_response,
            mock_content_response,
        ]
        with pytest.raises(ValueError, match="Invalid return_type. Must be 'bytes' or 'text'."):
            self.files_api.get_file_content(123, max_file_size_bytes=2048, return_type="invalid")

    def test_get_sql_schemas(self):
        """Test get_sql_schemas method correctly processes API data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tables": [
                {
                    "name": "history_items",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "url", "type": "TEXT"},
                    ],
                }
            ]
        }
        self.files_api.api_client.session.get.return_value = mock_response
        result = self.files_api.get_sql_schemas(123)
        assert "history_items" in [table["name"] for table in result["tables"]]

    def test_run_sql_query(self):
        """Test run_sql_query method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "columns": ["id", "url"],
            "rows": [[1, "http://example.com"], [2, "http://test.com"]],
        }
        self.files_api.api_client.session.post.return_value = mock_response
        query = "SELECT * FROM history_items LIMIT 2;"
        result = self.files_api.run_sql_query(123, query)
        assert result == {
            "columns": ["id", "url"],
            "rows": [[1, "http://example.com"], [2, "http://test.com"]],
        }
        self.files_api.api_client.session.post.assert_called_once_with(
            f"{self.api_client.base_url}/files/123/sql/query/", json={"query": query}
        )
