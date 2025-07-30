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

import json
from typing import Any

from openrelik_api_client.api_client import APIClient


class WorkflowsAPI:
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.folders_url = f"{self.api_client.base_url}/folders"

    def create_workflow(
        self, folder_id: int, file_ids: list, template_id: int = None
    ) -> int | None:
        """Creates a new workflow.

        Args:
            folder_id: The ID of the folder to create the workflow in.
            file_ids: A list of file IDs to associate with the workflow.
            template_id: The ID of the workflow template to use.

        Returns:
            The ID of the created workflow. None otherwise

        Raises:
            HTTPError: If the API request failed.
        """
        workflow_id = None
        endpoint = f"{self.folders_url}/{folder_id}/workflows/"
        data = {
            "folder_id": folder_id,
            "file_ids": file_ids,
            "template_id": template_id,
        }
        response = self.api_client.session.post(endpoint, json=data)
        response.raise_for_status()
        if response.status_code == 200:
            workflow_id = response.json().get("id")
        return workflow_id

    def get_workflow(self, folder_id: int, workflow_id: int) -> dict[str, Any]:
        """Retrieves a workflow by ID.

        Args:
            folder_id: The ID of the folder where the workflow exists.
            workflow_id: The ID of the workflow to retrieve.

        Returns:
            The workflow data.

         Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.folders_url}/{folder_id}/workflows/{workflow_id}"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()

    def get_workflow_status(self, folder_id: int, workflow_id: int) -> dict[str, Any]:
        """Retrieves a workflow status by ID.

        Args:
            folder_id: The ID of the folder where the workflow exists.
            workflow_id: The ID of the workflow to retrieve.

        Returns:
            The workflow status data.

         Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.folders_url}/{folder_id}/workflows/{workflow_id}/status"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()

    def update_workflow(
        self, folder_id: int, workflow_id: int, workflow_data: dict
    ) -> dict[str, Any] | None:
        """Updates an existing workflow.

        Args:
            folder_id: The ID of the folder containing the workflow.
            workflow_id: The ID of the workflow to update.
            workflow_data: The updated workflow data.

        Returns:
            The updated workflow data, or None.

        Raises:
            HTTPError: If the API request failed.
        """
        workflow = None
        endpoint = f"{self.folders_url}/{folder_id}/workflows/{workflow_id}"
        response = self.api_client.session.patch(endpoint, json=workflow_data)
        response.raise_for_status()
        if response.status_code == 200:
            workflow = response.json()
        return workflow

    def delete_workflow(self, folder_id, workflow_id) -> bool:
        """Deletes a workflow.

        Args:
            folder_id: The ID of the folder containing the workflow.
            workflow_id: The ID of the workflow to delete.

        Returns:
            True if the request was successful.

        Raises:
            HTTPError: If the API request failed.
        """
        endpoint = f"{self.folders_url}/{folder_id}/workflows/{workflow_id}"
        response = self.api_client.session.delete(endpoint)
        response.raise_for_status()
        return response.status_code == 204

    def run_workflow(self, folder_id: int, workflow_id: int) -> dict[str, Any] | None:
        """Runs an existing workflow.

        Args:
            folder_id: The ID of the folder containing the workflow.
            workflow_id: The ID of the workflow to run.
            run_data: Optional data to pass to the workflow run.

        Returns:
            A workflow object.

        Raises:
            HTTPError: If the API request failed.
        """
        workflow = None
        endpoint = f"{self.folders_url}/{folder_id}/workflows/{workflow_id}/run/"
        workflow = self.get_workflow(folder_id, workflow_id)
        spec = json.loads(workflow.get("spec_json"))
        data = {"workflow_spec": spec}
        response = self.api_client.session.post(endpoint, json=data)
        response.raise_for_status()
        if response.status_code == 200:
            workflow = response.json()
        return workflow
