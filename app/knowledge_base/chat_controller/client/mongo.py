from typing import Any, Dict
from pymongo import MongoClient
from app.knowledge_base.chat_controller.chat_database import ChatDatabase
from datetime import datetime

class MongoChatClient(ChatDatabase):
    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db_name: str = "chat_db",
    ):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.chats = self.db["chats"]
        self.messages = self.db["messages"]

    def add_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self.chats.insert_one({
                'created_at': datetime.now(),
            })
            return {"inserted_id": str(result.inserted_id)}
        except Exception as e:
            raise Exception(f"Error adding chat: {e}")

    def get_chat(self, chat_id: str) -> Dict[str, Any]:
        doc = self.chats.find_one({"chat_id": chat_id})
        return doc or {}

    def delete_chat(self, chat_id: str) -> None:
        self.chats.delete_one({"chat_id": chat_id})
        self.messages.delete_many({"chat_id": chat_id})

    def add_message(self, chat_id: str, message: Dict[str, Any]) -> None:
        msg = {"chat_id": chat_id, **message}
        self.messages.insert_one(msg)

    def get_messages(self, chat_id: str, limit: int = 100) -> list[Any]:
        messages = []
        cursor = self.messages.find({"chat_id": chat_id}).sort("_id", 1).limit(limit)
        for message in cursor:
            messages.append(message)
        return messages
