import pytest
from unittest.mock import MagicMock, patch
from requests.exceptions import HTTPError

from openrelik_api_client.api_client import APIClient
from openrelik_api_client.api_client import TokenRefreshSession
from openrelik_api_client.folders import FoldersAPI


class TestFoldersAPI:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = MagicMock(spec=APIClient)
        self.api_client.session = MagicMock(spec=TokenRefreshSession)
        self.api_client.base_url = "https://api.example.com/api/v1"
        self.folders_api = FoldersAPI(self.api_client)

    def test_init(self):
        """Test FoldersAPI initialization."""
        assert self.folders_api.api_client == self.api_client

    def test_create_root_folder(self):
        """Test create_root_folder method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123}
        self.api_client.session.post.return_value = mock_response

        # Execute
        folder_id = self.folders_api.create_root_folder("Test Folder")

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.api_client.base_url}/folders/",
            json={"display_name": "Test Folder"}
        )
        mock_response.raise_for_status.assert_called_once()
        assert folder_id == 123

    def test_create_root_folder_failure(self):
        """Test create_root_folder method when API returns non-201 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200  # Not 201
        mock_response.json.return_value = {"id": 123}
        self.api_client.session.post.return_value = mock_response

        # Execute
        folder_id = self.folders_api.create_root_folder("Test Folder")

        # Verify
        self.api_client.session.post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert folder_id is None

    def test_create_subfolder(self):
        """Test create_subfolder method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 456}
        self.api_client.session.post.return_value = mock_response

        # Execute
        folder_id = self.folders_api.create_subfolder(123, "Subfolder")

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123/folders/",
            json={"display_name": "Subfolder"}
        )
        mock_response.raise_for_status.assert_called_once()
        assert folder_id == 456

    def test_create_subfolder_failure(self):
        """Test create_subfolder method when API returns non-201 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200  # Not 201
        mock_response.json.return_value = {"id": 456}
        self.api_client.session.post.return_value = mock_response

        # Execute
        folder_id = self.folders_api.create_subfolder(123, "Subfolder")

        # Verify
        self.api_client.session.post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert folder_id is None

    def test_folder_exists_true(self):
        """Test folder_exists method when folder exists."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.folders_api.folder_exists(123)

        # Verify
        self.api_client.session.get.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result is True

    def test_folder_exists_false(self):
        """Test folder_exists method when folder doesn't exist."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.folders_api.folder_exists(123)

        # Verify
        self.api_client.session.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is False

    def test_update_folder(self):
        """Test update_folder method."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123, "display_name": "Updated Folder"}
        self.api_client.session.patch.return_value = mock_response

        folder_data = {"display_name": "Updated Folder"}

        # Execute
        result = self.folders_api.update_folder(123, folder_data)

        # Verify
        self.api_client.session.patch.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123",
            json=folder_data
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == {"id": 123, "display_name": "Updated Folder"}

    def test_delete_folder(self):
        """Test delete_folder method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 204
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.folders_api.delete_folder(123)

        # Verify
        self.api_client.session.delete.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result is True

    def test_delete_folder_failure(self):
        """Test delete_folder method when API returns non-204 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200  # Not 204
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.folders_api.delete_folder(123)

        # Verify
        self.api_client.session.delete.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is False

    def test_share_folder_with_users(self):
        """Test share_folder method with users."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        self.api_client.session.post.return_value = mock_response

        # Execute
        result = self.folders_api.share_folder(
            folder_id=123,
            user_names=["user1", "user2"],
            user_role="editor"
        )

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123/roles",
            json={
                "user_ids": [],
                "user_names": ["user1", "user2"],
                "group_ids": [],
                "group_names": [],
                "user_role": "editor",
                "group_role": "viewer"  # Default
            }
        )
        assert result == {"result": "success"}

    def test_share_folder_with_groups(self):
        """Test share_folder method with groups."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        self.api_client.session.post.return_value = mock_response

        # Execute
        result = self.folders_api.share_folder(
            folder_id=123,
            group_names=["group1", "group2"],
            group_role="editor"
        )

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123/roles",
            json={
                "user_ids": [],
                "user_names": [],
                "group_ids": [],
                "group_names": ["group1", "group2"],
                "user_role": "viewer",  # Default
                "group_role": "editor"
            }
        )
        assert result == {"result": "success"}

    def test_share_folder_with_ids(self):
        """Test share_folder method with user_ids and group_ids."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        self.api_client.session.post.return_value = mock_response

        # Execute
        result = self.folders_api.share_folder(
            folder_id=123,
            user_ids=[1, 2],
            group_ids=[3, 4]
        )

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.api_client.base_url}/folders/123/roles",
            json={
                "user_ids": [1, 2],
                "user_names": [],
                "group_ids": [3, 4],
                "group_names": [],
                "user_role": "viewer",  # Default
                "group_role": "viewer"  # Default
            }
        )
        assert result == {"result": "success"}

    def test_share_folder_api_error(self):
        """Test share_folder method when API returns an error."""
        # Setup
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"error": "Permission denied"}
        # Also mock .text in case .json() fails with ValueError
        mock_api_response.text = '{"error": "Permission denied"}'

        http_error = HTTPError("API Error")
        http_error.response = mock_api_response # Attach the mocked response to the error
        self.api_client.session.post.side_effect = http_error

        with patch('builtins.print') as mock_print:
            result = self.folders_api.share_folder(
                folder_id=123,
                user_names=["user1"]
            )

        # Verify
        self.api_client.session.post.assert_called_once()
        assert result is None
