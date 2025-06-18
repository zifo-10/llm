# This code initializes a knowledge base with a vector database and vector embedding service.
# It uses the Qdrant vector database and Cohere for vector embeddings.
from container import knowledge_base

knowledge_base.add_knowledge(
    query_text="What is the capital of France?",
    payload={"source": "Wikipedia", "category": "Geography"}
)




# # Example usage(How to use the knowledge base):
# knowledge_base.get_knowledge(
#     query_text="What is the capital of France?",
#     top_k=5
# )
