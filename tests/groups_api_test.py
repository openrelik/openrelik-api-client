import pytest
from unittest.mock import MagicMock, patch

from openrelik_api_client.api_client import APIClient
from openrelik_api_client.api_client import TokenRefreshSession
from openrelik_api_client.groups import GroupsAPI


class TestGroupsAPI:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = MagicMock(spec=APIClient)
        self.api_client.session = MagicMock(spec=TokenRefreshSession)
        self.api_client.base_url = "https://api.example.com/api/v1"
        self.groups_api = GroupsAPI(self.api_client)

    def test_init(self):
        """Test GroupsAPI initialization."""
        assert self.groups_api.api_client == self.api_client
        assert self.groups_api.groups_url == f"{self.api_client.base_url}/groups"

    def test_create_group(self):
        """Test create_group method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123, "name": "test_group"}
        self.api_client.session.post.return_value = mock_response

        # Execute
        result = self.groups_api.create_group(
            "test_group", "Test group description")

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.groups_api.groups_url}/",
            json={
                "name": "test_group",
                "description": "Test group description"
            }
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == {"id": 123, "name": "test_group"}

    def test_create_group_empty_name(self):
        """Test create_group method with empty name."""
        # Execute and verify
        with pytest.raises(ValueError, match="Group name cannot be empty."):
            self.groups_api.create_group("")

        # Verify that no API call was made
        self.api_client.session.post.assert_not_called()

    def test_create_group_failure(self):
        """Test create_group method when API returns non-201 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200  # Not 201
        mock_response.json.return_value = {"id": 123, "name": "test_group"}
        self.api_client.session.post.return_value = mock_response

        # Execute
        result = self.groups_api.create_group("test_group")

        # Verify
        self.api_client.session.post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is None

    def test_remove_group(self):
        """Test remove_group method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 204
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.groups_api.remove_group("test_group")

        # Verify
        self.api_client.session.delete.assert_called_once_with(
            f"{self.groups_api.groups_url}/test_group"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result is True

    def test_remove_group_failure(self):
        """Test remove_group method when API returns non-204 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200  # Not 204
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.groups_api.remove_group("test_group")

        # Verify
        self.api_client.session.delete.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is False

    def test_list_group_members(self):
        """Test list_group_members method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "username": "user1"},
            {"id": 2, "username": "user2"}
        ]
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.groups_api.list_group_members("test_group")

        # Verify
        self.api_client.session.get.assert_called_once_with(
            f"{self.groups_api.groups_url}/test_group/users"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == [
            {"id": 1, "username": "user1"},
            {"id": 2, "username": "user2"}
        ]

    def test_list_group_members_failure(self):
        """Test list_group_members method when API returns non-200 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.groups_api.list_group_members("test_group")

        # Verify
        self.api_client.session.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is None

    def test_list_groups(self):
        """Test list_groups method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "group1"},
            {"id": 2, "name": "group2"}
        ]
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.groups_api.list_groups()

        # Verify
        self.api_client.session.get.assert_called_once_with(
            f"{self.groups_api.groups_url}/"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == [
            {"id": 1, "name": "group1"},
            {"id": 2, "name": "group2"}
        ]

    def test_list_groups_failure(self):
        """Test list_groups method when API returns non-200 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 500
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.groups_api.list_groups()

        # Verify
        self.api_client.session.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result == []

    def test_delete_group(self):
        """Test delete_group method."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 204
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.groups_api.delete_group("test_group")

        # Verify
        self.api_client.session.delete.assert_called_once_with(
            f"{self.groups_api.groups_url}/test_group"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result is True

    def test_delete_group_failure(self):
        """Test delete_group method when API returns non-204 status code."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.groups_api.delete_group("test_group")

        # Verify
        self.api_client.session.delete.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is False

    def test_add_users_to_group(self):
        """Test add_users_to_group method."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = ["user1", "user2"]
        self.api_client.session.post.return_value = mock_response

        # Execute
        result = self.groups_api.add_users_to_group(
            "test_group", ["user1", "user2"])

        # Verify
        self.api_client.session.post.assert_called_once_with(
            f"{self.groups_api.groups_url}/test_group/users/",
            json=["user1", "user2"]
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == ["user1", "user2"]

    def test_remove_users_from_group(self):
        """Test remove_users_from_group method."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = ["user1", "user2"]
        self.api_client.session.delete.return_value = mock_response

        # Execute
        result = self.groups_api.remove_users_from_group(
            "test_group", ["user1", "user2"])

        # Verify
        self.api_client.session.delete.assert_called_once_with(
            f"{self.groups_api.groups_url}/test_group/users",
            json=["user1", "user2"]
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == ["user1", "user2"]

    def test_is_member_true(self):
        """Test is_member method when user is a member."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = [{"username": "user1"}]
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.groups_api.is_member("test_group", "user1")

        # Verify
        self.api_client.session.get.assert_called_once_with(
            f"{self.groups_api.groups_url}/test_group/users/"
        )
        mock_response.raise_for_status.assert_called_once()
        assert result is True

    def test_is_member_false(self):
        """Test is_member method when user is not a member."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = [{"username": "user2"}]
        self.api_client.session.get.return_value = mock_response

        # Execute
        result = self.groups_api.is_member("test_group", "user1")

        # Verify
        self.api_client.session.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert result is False
