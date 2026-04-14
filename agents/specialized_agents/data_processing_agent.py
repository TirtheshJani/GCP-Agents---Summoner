"""Data processing agent for GCS-based ETL tasks.

This agent:
1. Lists files in a Cloud Storage bucket/prefix.
2. Downloads and processes each file using a caller-supplied transform.
3. Uploads the results back to GCS under a configured output prefix.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import structlog

from agents.base_agent import BaseAgent
from config import Settings
from tools.gcp_tools import CloudStorageTool

logger = structlog.get_logger(__name__)

def _default_transform(data: bytes) -> bytes:
    """Default transform: return data unchanged."""
    return data


class DataProcessingAgent(BaseAgent):
    """Agent that processes files stored in Google Cloud Storage."""

    def __init__(
        self,
        settings: Settings | None = None,
        transform: Callable[[bytes], bytes] | None = None,
        source_prefix: str = "",
    ) -> None:
        super().__init__(settings)
        self._storage = CloudStorageTool(self.settings)
        self._transform = transform or _default_transform
        self._source_prefix = source_prefix

    @property
    def name(self) -> str:
        return "data-processing"

    def plan(self, task: str) -> str:
        """List blobs that match the source prefix and build a processing plan."""
        bucket = self.settings.storage.bucket
        blobs = self._storage.list_blobs(bucket, prefix=self._source_prefix)
        blob_names = [b.name for b in blobs]
        self.memory.set("source_blobs", blob_names)
        return json.dumps(
            {
                "task": task,
                "bucket": bucket,
                "source_prefix": self._source_prefix,
                "files_to_process": blob_names,
                "output_prefix": self.settings.storage.output_prefix,
            }
        )

    def execute(self, plan: str) -> Any:
        """Download, transform, and re-upload each file."""
        plan_data = json.loads(plan)
        bucket = plan_data["bucket"]
        output_prefix = plan_data["output_prefix"]
        processed: list[str] = []

        for blob_name in plan_data["files_to_process"]:
            raw = self._storage.download(bucket, blob_name)
            transformed = self._transform(raw)
            dest = f"{output_prefix}{blob_name.rsplit('/', 1)[-1]}"
            self._storage.upload(bucket, dest, transformed)
            processed.append(dest)
            logger.info("file.processed", source=blob_name, dest=dest)

        return {"processed_files": processed, "count": len(processed)}

    def reflect(self, task: str, result: Any) -> bool:
        """Succeed if at least one file was processed (or no files existed)."""
        if not isinstance(result, dict):
            return False
        return True
