from knowledge_base.vector_embedding.client.cohere_embedding import CohereEmbeddingClient
from knowledge_base.vector_embedding.client.huggingface_embedding import HuggingFaceEmbeddingClient
from knowledge_base.vector_embedding.vector_embedding import VectorEmbedding


class EmbedEnum:
    """
    Enum class for different types of vector embedding models.
    """
    OPENAI = 'openai'
    HUGGINGFACE = 'huggingface'
    COHERE = 'cohere'
    # Add more embedding model types as needed


class VectorEmbeddingFactory:
    """
    Factory class for creating vector embedding instances.
    """

    @staticmethod
    def create_vector_embedding(embed_type: str, **kwargs) -> 'VectorEmbedding':
        """
        Create a vector embedding instance based on the specified type.

        :param embed_type: Type of the vector embedding model (e.g., 'openai', 'huggingface').
        :param kwargs: Additional parameters for the embedding model initialization.
        :return: An instance of the specified vector embedding model.
        """
        if embed_type == EmbedEnum.COHERE:
            try:
                if 'api_key' not in kwargs:
                    raise ValueError("API key is required for Cohere embedding client.")
                return CohereEmbeddingClient(api_key=kwargs['api_key'])
            except Exception as e:
                raise ValueError(f"Failed to create Cohere embedding client: {e}")
        if embed_type == EmbedEnum.HUGGINGFACE:
            try:
                if 'model' not in kwargs:
                    raise ValueError("Model is required for HuggingFace embedding client.")
                return HuggingFaceEmbeddingClient(model=kwargs['model'])
            except Exception as e:
                raise ValueError(f"Failed to create HuggingFace embedding client: {e}")
        else:
            raise ValueError(f"Unsupported vector embedding type: {embed_type}. "
                             f"Supported types are: {', '.join(EmbedEnum.__dict__.keys())}.")
