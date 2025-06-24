from abc import abstractmethod, ABC
from typing import Any, Dict


class ChatDatabase(ABC):
    """
    Abstract base class for Chat databases.
    """

    @abstractmethod
    def add_message(
        self,
        chat_id: str,
        message: Dict[str, Any],
    ) -> None:
        """
        Add a message to the chat database.

        :param chat_id: Unique identifier for the chat.
        :param message: Message data to be added.
        """
        pass

    @abstractmethod
    def get_messages(
        self,
        chat_id: str,
        limit: int = 100,
    ) -> list[Any]:
        """
        Retrieve messages from the chat database.

        :param chat_id: Unique identifier for the chat.
        :param limit: Maximum number of messages to retrieve.
        :return: Messages from the chat database.
        """
        pass

    @abstractmethod
    def delete_chat(
        self,
        chat_id: str,
    ) -> None:
        """
        Delete a chat from the database.

        :param chat_id: Unique identifier for the chat to be deleted.
        """
        pass

    @abstractmethod
    def add_chat(
        self,
        chat_data: Dict[str, Any],
    ) -> dict:
        """
        Add a new chat to the database.

        :param chat_data: Data associated with the chat.
        """
        pass

    @abstractmethod
    def get_chat(
        self,
        chat_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve a chat from the database.

        :param chat_id: Unique identifier for the chat.
        :return: Data associated with the chat.
        """
        pass