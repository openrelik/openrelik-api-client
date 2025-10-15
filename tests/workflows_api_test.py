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
from openrelik_api_client.workflows import WorkflowsAPI


class TestWorkflowAPI:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = MagicMock(spec=APIClient)
        self.api_client.session = MagicMock(spec=TokenRefreshSession)
        self.api_client.base_url = "https://api.example.com/api/v1"
        self.workflows_api = WorkflowsAPI(self.api_client)

    def test_init(self):
        """Test initialization."""
        assert self.workflows_api.api_client == self.api_client

    def test_create_workflow_reports(self):
        """Test create_workflow_reports method."""

        def test_get_workflow_report(self):
            """Test get_workflow_report method."""
            workflow_id = 123
            mock_response = MagicMock()
            mock_response.status_code = 200
            expected_report = {"id": workflow_id, "status": "completed", "data": {}}
            mock_response.json.return_value = expected_report
            self.api_client.session.get.return_value = mock_response

            report = self.workflows_api.get_workflow_report(workflow_id)

            self.api_client.session.get.assert_called_once_with(
                f"{self.api_client.base_url}/workflows/{workflow_id}/report/"
            )
            mock_response.raise_for_status.assert_called_once()
            assert report == expected_report

        def test_get_workflow_report_no_content(self):
            """Test get_workflow_report method when no content is returned."""
            workflow_id = 456
            mock_response = MagicMock()
            mock_response.status_code = 204
            self.api_client.session.get.return_value = mock_response

            report = self.workflows_api.get_workflow_report(workflow_id)

            self.api_client.session.get.assert_called_once_with(
                f"{self.api_client.base_url}/workflows/{workflow_id}/report/"
            )
            mock_response.raise_for_status.assert_called_once()
            mock_response.json.assert_not_called()
            assert report is None
