from typing import Optional, Any

from app.knowledge_base.chat_controller.chat_database import ChatDatabase
from app.knowledge_base.vector_database.vector_database import VectorDatabase
from app.knowledge_base.vector_embedding.vector_embedding import VectorEmbedding


class KnowledgeBase:
    def __init__(self, vector_embeddings: VectorEmbedding,
                 vector_database: VectorDatabase,
                 chat_database: Optional[ChatDatabase] = None):
        """Initialize the KnowledgeBase with vector embeddings and a vector database."""
        self.vector_embeddings = vector_embeddings
        self.vector_database = vector_database
        self.chat_database = chat_database

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

    def get_knowledge(self, query_text: str, top_k: int = 10, score_threshold: float = None):
        try:
            query_vector = self.vector_embeddings.embed(query_text)
            results = self.vector_database.vector_search(collection_name="knowledge_base",
                                                         query_vector=query_vector,
                                                         top_k=top_k,
                                                         score_threshold=score_threshold)
            return results
        except Exception as e:
            print(f"Error retrieving knowledge: {e}")
            raise e

    def add_chat(self, chat_data: dict = None) -> str:
        """
        Add a chat to the chat database.
        """
        try:
            if self.chat_database:
                result = self.chat_database.add_chat(chat_data)
                return result['inserted_id'] if 'inserted_id' in result else result
            else:
                raise ValueError("Chat database is not initialized.")
        except Exception as e:
            print(f"Error adding chat: {e}")
            raise e

    def get_messages(self, chat_id: str, limit: int = 100) -> list[Any]:
        """
        Retrieve messages from the chat database.
        """
        try:
            print(f"Retrieving chat history for chat_id: {chat_id}")
            messages_list = []
            if self.chat_database:
                messages = self.chat_database.get_messages(chat_id, limit)
                for message in messages:
                    messages_list.append({
                        "role": message["role"],
                        "content": message["content"],
                    })
                return messages_list
            else:
                raise ValueError("Chat database is not initialized.")
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            raise e

    def add_message(self, chat_id: str, message: dict):
        """
        Add a message to the chat database.
        """
        try:
            if self.chat_database:
                self.chat_database.add_message(chat_id, message)
            else:
                raise ValueError("Chat database is not initialized.")
        except Exception as e:
            print(f"Error adding message: {e}")
            raise e
