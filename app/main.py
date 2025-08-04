import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.constant import Constant
from app.container import knowledge_base, llm_client

logging.basicConfig(
    level=logging.INFO,  # or DEBUG for more detail
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KnowledgeItem(BaseModel):
    question: str = Field(..., description="The question to be answered")
    title: str = Field(..., description="Title of the knowledge item")
    answer: str = Field(..., description="The answer to the question")
    source: Optional[List[str]] = Field(None, description="Source of the knowledge item")
    published_at: str = Field(..., description="Publication date of the knowledge item")


@app.post("/knowledge")
async def bulk_upload_knowledge(knowledge_request: KnowledgeItem):
    try:
        query_text = (
            f"العنوان: {knowledge_request.title}\n"
            f"السؤال: {knowledge_request.question}\n"
            f"الإجابة: {knowledge_request.answer}"
        )

        payload = {
            "title": knowledge_request.title,
            "question": knowledge_request.question,
            "answer": knowledge_request.answer,
            "source": knowledge_request.source,
            "published_at": knowledge_request.published_at,
        }
        # Add to knowledge base
        knowledge_base.add_knowledge(
            query_text=query_text,
            payload=payload
        )
        return {"message": "Processing completed."}

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.get("/knowledge/search")
async def search_knowledge(query: str, top_k: int = 5, score_threshold: float = None):
    try:
        # Example usage(How to use the knowledge base):
        knowledge = knowledge_base.get_knowledge(
            query_text=query,
            top_k=top_k,
            score_threshold=score_threshold
        )
        if not knowledge:
            return JSONResponse(status_code=404, content={"message": "No knowledge found."})
        knowledge_list = []
        for item in knowledge:
            knowledge_list.append(item.payload)

        return {"knowledge": knowledge_list}

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/chat")
async def chat_with_llm(
    query: str,
    temperature: float = 0.7,
    chat_id: str = None,
    top_k: int = 5,
    score_threshold: float = 0.4
):
    try:
        logger.info(f"Chat started. Query: {query} | Chat ID: {chat_id}")

        # Start messages with system prompt
        messages = [{
            "role": "system",
            "content": Constant.SYSTEM_PROMPT
        }]

        search_query = query

        # If there is chat history, use it to build context
        if chat_id:
            history = knowledge_base.get_messages(chat_id)

            if history:
                messages.extend(history[-4:])  # Add recent messages

                # Collect last two user messages
                user_msgs = [msg['content'] for msg in history if msg['role'] == 'user']
                last_two = user_msgs[-2:] if len(user_msgs) >= 2 else user_msgs

                # Combine with current query
                search_query = "\n".join(last_two + [query])
        else:
            # Create new chat session
            chat_id = str(knowledge_base.add_chat())
            logger.info(f"New chat started with ID: {chat_id}")

        # Get relevant knowledge
        knowledge = knowledge_base.get_knowledge(
            query_text=search_query,
            top_k=top_k,
            score_threshold=score_threshold
        )

        # Separate knowledge and sources
        knowledge_list = []
        sources_set = set()

        if knowledge:
            for item in knowledge:
                payload = item.payload.copy()
                sources = payload.get("source", [])
                sources_set.update(sources)
                payload.pop("source", None)
                knowledge_list.append(payload)

        # Convert set back to list
        sources_list = list(sources_set)

        # Construct user message for LLM
        user_query = {
            "role": "user",
            "content": f"##Knowledge: {knowledge_list}\n\n##User Query: {query}"
        }
        messages.append(user_query)

        # Call LLM
        response = llm_client.chat(messages=messages, temperature=temperature)
        answer = response["choices"][0]["message"]["content"]

        # Save messages to history
        now = datetime.now().isoformat()
        knowledge_base.add_message(chat_id=chat_id, message={"role": "user", "content": query, "time": now})
        knowledge_base.add_message(chat_id=chat_id, message={"role": "assistant", "content": answer, "time": now})

        logger.info(f"Chat completed for chat_id={chat_id}")
        return {"chat_id": chat_id, "answer": answer, "sources": sources_list}

    except Exception as e:
        logger.exception("LLM chat failed")
        return JSONResponse(status_code=400, content={"error": str(e)})

