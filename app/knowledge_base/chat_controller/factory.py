from .chat_database import ChatDatabase
from .client.mongo import MongoChatClient


class ChatDatabaseEnum:
    """
    Enum class for different types of chat databases.
    """
    SQLITE = 'sqlite'
    MONGODB = 'mongodb'
    # Add more database types as needed


class ChatDatabaseFactory:
    """
    Factory class for creating chat database instances.
    """

    @staticmethod
    def create_chat_database(db_type: str, **kwargs) -> 'ChatDatabase':
        """
        Create a chat database instance based on the specified type.

        :param db_type: Type of the chat database (e.g., 'sqlite', 'mongodb').
        :param kwargs: Additional parameters for the database connection.
        :return: An instance of a chat database.
        """
        if db_type == 'mongodb':
            try:
                return MongoChatClient(**kwargs)
            except Exception as e:
                raise Exception(f"Error creating MongoDB chat client: {str(e)}")
        else:
            raise ValueError(f"Unsupported chat database type: {db_type}")
