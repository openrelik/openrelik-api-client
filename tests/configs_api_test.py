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

from unittest.mock import MagicMock

from openrelik_api_client.api_client import APIClient, TokenRefreshSession
from openrelik_api_client.configs import ConfigsAPI


class TestAPIClient:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = MagicMock(spec=APIClient)
        self.api_client.session = MagicMock(spec=TokenRefreshSession)
        self.api_client.base_url = "https://api.example.com/api/v1"
        self.configs_api = ConfigsAPI(self.api_client)

    def test_init(self):
        """Test FoldersAPI initialization."""
        assert self.configs_api.api_client == self.api_client

    def test_get_system_config(self):
        """Test get_system_config method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"config": "value"}
        self.configs_api.api_client.session.get.return_value = mock_response

        config = self.configs_api.get_system_config()

        self.configs_api.api_client.session.get.assert_called_once_with(
            "https://api.example.com/api/v1/configs/system/"
        )
        mock_response.raise_for_status.assert_called_once()
        assert config == {"config": "value"}
