import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.conversions.common_types import (
    UpdateResult,
)
from qdrant_client.http.models import (
    ScoredPoint
)

from knowledge_base.vector_database.vector_database import VectorDatabase


class QdrantDBClient(VectorDatabase):
    """
    Singleton class for managing interactions with a Qdrant vector database.
    """

    def __init__(self, host: str, port: int, vector_size: int = 1024):
        try:
            self.client = QdrantClient(url=host, port=port)
            check_collection = self.client.collection_exists(collection_name="knowledge_base")
            if not check_collection:
                self.client.create_collection(
                    collection_name="knowledge_base",
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                )

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Qdrant database, please provide valid host and port. Error: {e}")

    def insert_item(self,
                    collection_name: str,
                    vector: List[float],
                    metadata: dict = None,
                    ) -> UpdateResult:
        try:
            print('collection name', collection_name)
            result = self.client.upsert(
                collection_name=collection_name,
                points=[models.PointStruct(
                    id=str(uuid.uuid4()),
                    payload=metadata,
                    vector=vector
                )
                ]
            )
            print('results************', result)
            return result
        except Exception as e:
            raise e

    def vector_search(
            self, collection_name: str, query_vector: list[float], top_k: int = 10
    ) -> List[ScoredPoint]:
        try:
            result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            return result
        except Exception as e:
            raise e
