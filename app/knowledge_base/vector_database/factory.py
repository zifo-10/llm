from app.knowledge_base.vector_database.client.qdrant import QdrantDBClient
from app.knowledge_base.vector_database.vector_database import VectorDatabase


class VectorDatabaseEnum:
    """
    Enum class for different types of vector databases.
    """
    QDRANT = 'qdrant'
    FAISS = 'faiss'
    WEAVIATE = 'weaviate'
    # Add more vector database types as needed


class VectorDatabaseFactory:
    """
    Factory class for creating vector database instances.
    """

    @staticmethod
    def create_vector_database(db_type: str, **kwargs) -> 'VectorDatabase':
        """
        Create a vector database instance based on the specified type.

        :param db_type: Type of the vector database (e.g., 'faiss', 'weaviate').
        :param kwargs: Additional parameters for the database initialization.
        :return: An instance of the specified vector database.
        """
        if db_type == VectorDatabaseEnum.QDRANT:
            return QdrantDBClient(**kwargs)
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}. "
                             f"Supported types are: {', '.join(VectorDatabaseEnum.__dict__.keys())}.")
