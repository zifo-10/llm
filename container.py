from knowledge_base.knowledge_base import KnowledgeBase
from knowledge_base.vector_database.factory import VectorDatabaseFactory
from knowledge_base.vector_embedding.factory import VectorEmbeddingFactory

vector_database = VectorDatabaseFactory().create_vector_database(
    db_type="qdrant",
    host="localhost",
    port=6333,
    vector_size=1024
)

cohere_vector_embedding = VectorEmbeddingFactory().create_vector_embedding(
    embed_type="cohere",
    api_key="your_cohere_api_key_here",
)

huggingface_vector_embedding = VectorEmbeddingFactory().create_vector_embedding(
    embed_type="huggingface",
    model="Qwen/Qwen3-Embedding-0.6B",
)

knowledge_base = KnowledgeBase(vector_embeddings=huggingface_vector_embedding,
                               vector_database=vector_database)
