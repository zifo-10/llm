import os
from dotenv import load_dotenv

from app.knowledge_base.chat_controller.factory import ChatDatabaseFactory
from app.knowledge_base.knowledge_base import KnowledgeBase
from app.knowledge_base.vector_database.factory import VectorDatabaseFactory
from app.knowledge_base.vector_embedding.factory import VectorEmbeddingFactory
from app.generation.client.llm_client import LLMClient

# Load environment variables
load_dotenv()

# Retrieve environment variables
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
cohere_api_key = os.getenv("COHERE_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
mongo_db_name = os.getenv("MONGO_DB_NAME")
llm_url = os.getenv("LLM_URL")

# Construct objects
vector_database = VectorDatabaseFactory().create_vector_database(
    db_type="qdrant",
    host=qdrant_host,
    port=qdrant_port,
    vector_size=1024
)

cohere_vector_embedding = VectorEmbeddingFactory().create_vector_embedding(
    embed_type="cohere",
    api_key=cohere_api_key,
)

mongo_chat_database = ChatDatabaseFactory().create_chat_database(
    db_type="mongodb",
    uri=mongo_uri,
    db_name=mongo_db_name
)

knowledge_base = KnowledgeBase(
    vector_embeddings=cohere_vector_embedding,
    vector_database=vector_database,
    chat_database=mongo_chat_database
)

llm_client = LLMClient(
    api_url=llm_url,
)

