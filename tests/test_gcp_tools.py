"""Tests for GCP tool wrappers (using mocks -- no GCP credentials needed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from config import Settings
from tools.gcp_tools import (
    CloudStorageTool,
    FirestoreTool,
    PubSubTool,
    VertexAITool,
)


@pytest.fixture
def settings():
    return Settings(
        gcp={"project_id": "test-project", "region": "us-central1"},
        storage={"bucket": "test-bucket"},
        firestore={"collection": "test-memory"},
    )


# ---------------------------------------------------------------------------
# VertexAITool
# ---------------------------------------------------------------------------


class TestVertexAITool:
    @patch("tools.gcp_tools.VertexAITool._get_model")
    def test_generate(self, mock_get_model, settings):
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="Generated answer")
        mock_get_model.return_value = mock_model

        tool = VertexAITool(settings)
        result = tool.generate("What is AI?")

        assert result == "Generated answer"
        mock_model.generate_content.assert_called_once()


# ---------------------------------------------------------------------------
# CloudStorageTool
# ---------------------------------------------------------------------------


class TestCloudStorageTool:
    @patch("tools.gcp_tools.CloudStorageTool._get_client")
    def test_upload(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_blob = MagicMock()
        mock_client.bucket.return_value.blob.return_value = mock_blob
        mock_get_client.return_value = mock_client

        tool = CloudStorageTool(settings)
        uri = tool.upload("my-bucket", "path/file.txt", b"data")

        assert uri == "gs://my-bucket/path/file.txt"
        mock_blob.upload_from_string.assert_called_once_with(b"data")

    @patch("tools.gcp_tools.CloudStorageTool._get_client")
    def test_download(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = b"file contents"
        mock_client.bucket.return_value.blob.return_value = mock_blob
        mock_get_client.return_value = mock_client

        tool = CloudStorageTool(settings)
        data = tool.download("my-bucket", "path/file.txt")

        assert data == b"file contents"

    @patch("tools.gcp_tools.CloudStorageTool._get_client")
    def test_list_blobs(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_client.list_blobs.return_value = ["blob1", "blob2"]
        mock_get_client.return_value = mock_client

        tool = CloudStorageTool(settings)
        blobs = tool.list_blobs("bucket", prefix="data/")

        assert blobs == ["blob1", "blob2"]
        mock_client.list_blobs.assert_called_once_with("bucket", prefix="data/")


# ---------------------------------------------------------------------------
# PubSubTool
# ---------------------------------------------------------------------------


class TestPubSubTool:
    @patch("tools.gcp_tools.PubSubTool._get_publisher")
    def test_publish(self, mock_get_publisher, settings):
        mock_publisher = MagicMock()
        mock_publisher.topic_path.return_value = "projects/test-project/topics/my-topic"
        mock_publisher.publish.return_value = MagicMock(
            result=MagicMock(return_value="msg-123")
        )
        mock_get_publisher.return_value = mock_publisher

        tool = PubSubTool(settings)
        msg_id = tool.publish("my-topic", b"hello")

        assert msg_id == "msg-123"


# ---------------------------------------------------------------------------
# FirestoreTool
# ---------------------------------------------------------------------------


class TestFirestoreTool:
    @patch("tools.gcp_tools.FirestoreTool._get_client")
    def test_save(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        tool = FirestoreTool(settings)
        tool.save("doc1", {"key": "value"})

        mock_client.collection.assert_called_once_with("test-memory")
        mock_client.collection.return_value.document.assert_called_once_with("doc1")

    @patch("tools.gcp_tools.FirestoreTool._get_client")
    def test_load_existing(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"key": "value"}
        mock_client.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        mock_get_client.return_value = mock_client

        tool = FirestoreTool(settings)
        data = tool.load("doc1")

        assert data == {"key": "value"}

    @patch("tools.gcp_tools.FirestoreTool._get_client")
    def test_load_missing(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        mock_get_client.return_value = mock_client

        tool = FirestoreTool(settings)
        data = tool.load("nonexistent")

        assert data is None

    @patch("tools.gcp_tools.FirestoreTool._get_client")
    def test_delete(self, mock_get_client, settings):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        tool = FirestoreTool(settings)
        tool.delete("doc1")

        mock_client.collection.return_value.document.return_value.delete.assert_called_once()
