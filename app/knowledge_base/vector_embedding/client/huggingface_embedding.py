# from sentence_transformers import SentenceTransformer
from app.knowledge_base.vector_embedding.vector_embedding import VectorEmbedding

class HuggingFaceEmbeddingClient(VectorEmbedding):
    def __init__(self, model: str = "Qwen/Qwen3-Embedding-0.6B") -> None:
        """
        Initializes the HuggingFace embedding client with the provided model.
        """
        # self.client = SentenceTransformer(model)

    def embed(self, text: str) -> list[float]:
        """
        Convert a single text input to a vector representation.

        Args:
            text (str): The input text to be embedded.

        Returns:
            list[float]: The vector representation of the input text.
        """
        try:
            embedding = self.client.encode(text, convert_to_numpy=True)  # shape: (dim,)
            return embedding.tolist()  # Convert from numpy to list[float]
        except Exception as e:
            print(f"Embedding error: {e}")
            raise e
