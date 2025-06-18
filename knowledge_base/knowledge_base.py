from knowledge_base.vector_database.vector_database import VectorDatabase
from knowledge_base.vector_embedding.vector_embedding import VectorEmbedding


class KnowledgeBase:
    def __init__(self, vector_embeddings: VectorEmbedding, vector_database: VectorDatabase):
        """Initialize the KnowledgeBase with vector embeddings and a vector database."""
        self.vector_embeddings = vector_embeddings
        self.vector_database = vector_database

    def add_knowledge(self, query_text: str, payload: dict):
        """
        Add knowledge to the knowledge base by embedding the query text and storing it in the vector database.
        """
        try:
            vector = self.vector_embeddings.embed(query_text)
            self.vector_database.insert_item("knowledge_base", vector=vector, metadata=payload)
        except Exception as e:
            print(f"Error adding knowledge: {e}")
            raise e

    def get_knowledge(self, query_text: str, top_k: int = 10):
        try:
            query_vector = self.vector_embeddings.embed(query_text)
            results = self.vector_database.vector_search(collection_name="knowledge_base",
                                                         query_vector=query_vector,
                                                         top_k=top_k)
            return results
        except Exception as e:
            print(f"Error retrieving knowledge: {e}")
            raise e
