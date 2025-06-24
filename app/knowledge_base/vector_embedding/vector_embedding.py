from abc import ABC, abstractmethod


class VectorEmbedding(ABC):
    """
    Abstract base class for vector embedding models.
    """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Convert text to a vector representation.

        Args:
            text (str): The input text to be embedded.

        Returns:
            list[float]: The vector representation of the input text.
        """
        pass
