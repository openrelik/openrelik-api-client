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

import math
import os
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from requests_toolbelt import MultipartEncoder

if TYPE_CHECKING:
    from openrelik_api_client.api_client import APIClient


class FilesAPI:
    def __init__(self, api_client: "APIClient"):
        super().__init__()
        self.api_client = api_client

    def download_file(self, file_id: int, filename: str) -> str | None:
        """Downloads a file from OpenRelik.

        Args:
            file_id: The ID of the file to download.
            filename: The name of the file to download.

        Returns:
            str: The path to the downloaded file.
        """
        endpoint = f"{self.api_client.base_url}/files/{file_id}/download"
        response = self.api_client.session.get(endpoint)
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
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/folders/{folder_id}"
            )
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
                    response = self.api_client.session.post(
                        f"{self.api_client.base_url}{endpoint}",
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
