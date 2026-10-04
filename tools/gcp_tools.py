"""Thin wrappers around Google Cloud client libraries.

Each tool class initialises its client lazily and exposes a small, focused API
that agents can call without worrying about GCP specifics.
"""

from __future__ import annotations

from typing import Any

import structlog

from config import Settings

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Vertex AI
# ---------------------------------------------------------------------------


class VertexAITool:
    """Generate text using a Vertex AI generative model."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(
                project=self._settings.gcp.project_id,
                location=self._settings.gcp.region,
            )
            self._model = GenerativeModel(self._settings.vertex_ai.model_name)
        return self._model

    def generate(self, prompt: str) -> str:
        """Send *prompt* to Vertex AI and return the response text."""
        model = self._get_model()
        cfg = self._settings.vertex_ai
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": cfg.temperature,
                "max_output_tokens": cfg.max_output_tokens,
                "top_p": cfg.top_p,
            },
        )
        text = response.text
        logger.info("vertexai.generate", chars=len(text))
        return text


# ---------------------------------------------------------------------------
# Cloud Storage
# ---------------------------------------------------------------------------


class CloudStorageTool:
    """Read, write, and list objects in Google Cloud Storage."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import storage

            self._client = storage.Client(project=self._settings.gcp.project_id)
        return self._client

    def upload(self, bucket_name: str, blob_name: str, data: bytes) -> str:
        """Upload *data* to ``gs://bucket_name/blob_name``. Returns the GCS URI."""
        client = self._get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data)
        uri = f"gs://{bucket_name}/{blob_name}"
        logger.info("gcs.upload", uri=uri, bytes=len(data))
        return uri

    def download(self, bucket_name: str, blob_name: str) -> bytes:
        """Download and return the contents of a GCS object."""
        client = self._get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        data = blob.download_as_bytes()
        logger.info("gcs.download", blob=blob_name, bytes=len(data))
        return data

    def list_blobs(self, bucket_name: str, prefix: str = "") -> list[Any]:
        """List blobs in *bucket_name* matching *prefix*."""
        client = self._get_client()
        return list(client.list_blobs(bucket_name, prefix=prefix))


# ---------------------------------------------------------------------------
# Pub/Sub
# ---------------------------------------------------------------------------


class PubSubTool:
    """Publish and subscribe to Google Cloud Pub/Sub topics."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._publisher: Any = None

    def _get_publisher(self) -> Any:
        if self._publisher is None:
            from google.cloud import pubsub_v1

            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    def publish(self, topic_id: str, data: bytes, **attrs: str) -> str:
        """Publish a message to a Pub/Sub topic. Returns the message ID."""
        publisher = self._get_publisher()
        topic_path = publisher.topic_path(self._settings.gcp.project_id, topic_id)
        future = publisher.publish(topic_path, data, **attrs)
        message_id = future.result()
        logger.info("pubsub.publish", topic=topic_id, message_id=message_id)
        return message_id


# ---------------------------------------------------------------------------
# Firestore
# ---------------------------------------------------------------------------


class FirestoreTool:
    """Persist and retrieve agent memory in Cloud Firestore."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(project=self._settings.gcp.project_id)
        return self._client

    def save(self, doc_id: str, data: dict[str, Any]) -> None:
        """Write *data* to the configured Firestore collection."""
        client = self._get_client()
        collection = self._settings.firestore.collection
        client.collection(collection).document(doc_id).set(data)
        logger.info("firestore.save", collection=collection, doc_id=doc_id)

    def load(self, doc_id: str) -> dict[str, Any] | None:
        """Load a document by ID. Returns ``None`` if it does not exist."""
        client = self._get_client()
        collection = self._settings.firestore.collection
        doc = client.collection(collection).document(doc_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def delete(self, doc_id: str) -> None:
        """Delete a document from the collection."""
        client = self._get_client()
        collection = self._settings.firestore.collection
        client.collection(collection).document(doc_id).delete()
        logger.info("firestore.delete", collection=collection, doc_id=doc_id)
