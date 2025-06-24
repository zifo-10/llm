import cohere
from app.knowledge_base.vector_embedding.vector_embedding import VectorEmbedding


class CohereEmbeddingClient(VectorEmbedding):
    def __init__(
            self,
            api_key: str,
            model: str = "embed-multilingual-v3.0"
    ) -> None:
        """
        Initializes the Cohere embedding client with the provided API key and model.

        Args:
            api_key (str): The API key for accessing Cohere services.
            model (str): The model to use for embedding generation.
        """
        self.client = cohere.ClientV2(api_key=api_key)
        self.model = model

    def embed(self, text: str) -> list[float]:
        """
        Convert text to a vector representation.

        Args:
            text (str): The input text to be embedded.

        Returns:
            list[float]: The vector representation of the input text.
        """
        try:
            response = self.client.embed(
                model=self.model,
                texts=[text],
                input_type="search_document",
                embedding_types=["float"],
            )
            return response.embeddings.float[0]
        except Exception as e:
            raise e
