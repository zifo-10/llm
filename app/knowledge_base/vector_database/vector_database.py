from abc import abstractmethod, ABC
from typing import Any, Dict


class VectorDatabase(ABC):
    """
    Abstract base class for vector databases.
    """

    @abstractmethod
    def insert_item(self, collection_name: str, vector: list[float], metadata: dict = None) -> Dict[str, Any]:
        """
        Insert a vector into the database.

        Args:
            collection_name (str): The name of the collection where the vector will be stored.
            vector (list[float]): The vector to insert.
            metadata (dict): Optional metadata associated with the vector.

        Returns:
            str: A unique identifier for the inserted vector.
        """
        pass

    @abstractmethod
    def vector_search(self, collection_name: str, query_vector: list[float],
                      top_k: int = 10, score_threshold: float = None) -> list[Any]:
        """
        Search for similar vectors in the database.

        Args:
            collection_name (str): The name of the collection to search in.
            query_vector (list[float]): The vector to search for.
            top_k (int): The number of top results to return.
            score_threshold (float): Optional threshold for filtering results based on similarity score.

        Returns:
            list[dict]: A list of dictionaries containing the matching vectors and their metadata.
        """
        pass
