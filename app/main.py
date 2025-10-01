import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

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
            knowledge_list.append({"payload": item.payload, "score": item.score, "id": item.id})

        return {"knowledge": knowledge_list}

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.delete("/knowledge/{point_id}")
async def delete_knowledge_point(point_id: str):
    try:
        result = knowledge_base.delete_knowledge_point(point_id=point_id)
        return {"message": "Knowledge point deleted successfully.", "result": result}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))


@app.post("/chat")
async def chat_with_llm(
        query: str,
        temperature: float = 0.2,
        chat_id: str = None,
        top_k: int = 10,
        score_threshold: float = 0.4
):
    try:
        logger.info(f"Chat started. Query: {query} | Chat ID: {chat_id}")

        # System prompt initialization
        messages = [{
            "role": "system",
            "content": Constant.SYSTEM_PROMPT
        }]
        fine_tuned_messages = [{
            "role": "system",
            "content": Constant.FINE_TUNED_PROMPT
        }]

        search_query = query

        # Use history if available
        if chat_id:
            history = knowledge_base.get_messages(chat_id)
            if history:
                # Keep last 4 messages in context
                messages.extend(history[-4:])
                fine_tuned_messages.extend(history[-4:])

                # Use last two user queries + current query for vector search
                user_msgs = [msg['content'] for msg in history if msg['role'] == 'user']
                last_two = user_msgs[-2:] if len(user_msgs) >= 2 else user_msgs
                search_query = "\n".join(last_two + [query])
        else:
            chat_id = str(knowledge_base.add_chat())
            logger.info(f"New chat started with ID: {chat_id}")

        # --- Knowledge search ---
        knowledge = knowledge_base.get_knowledge(
            query_text=search_query,
            top_k=top_k,
            score_threshold=score_threshold
        )

        knowledge_list = []
        sources_set = set()

        if knowledge:
            for item in knowledge:
                try:
                    payload = item.payload.copy()
                except Exception:
                    continue  # skip broken payloads

                # Defensive: source can be missing, None, or a single string
                raw_sources = payload.get("source", [])
                if raw_sources is None:
                    raw_sources = []
                elif isinstance(raw_sources, str):
                    raw_sources = [raw_sources]

                normalized_sources = [normalize_url(src) for src in raw_sources if src]
                sources_set.update(normalized_sources)

                # Don’t duplicate source inside knowledge payload
                payload.pop("source", None)
                knowledge_list.append(payload)

        sources_list = sorted(sources_set)

        # --- Final user query with retrieved knowledge ---
        user_query = {
            "role": "user",
            "content": f"##Knowledge: {knowledge_list}\n\n##User Query: {query}"
        }
        messages.append(user_query)

        # --- LLM call ---
        response = llm_client.chat(messages=messages, temperature=temperature)
        answer = response["choices"][0]["message"]["content"]

        # --- Check LLM response ---
        query_with_answer = {
            "role": "user",
            "content": f"Here is the knowledge: {knowledge_list}\n\nHere is the user query: {query}\n\nHere is the draft answer: {answer}\n\nPlease refine the draft answer according to the rules."
        }
        fine_tuned_messages.append(query_with_answer)
        fine_tuned_llm = llm_client.chat(messages=fine_tuned_messages, temperature=temperature)
        fine_tuned_answer = fine_tuned_llm["choices"][0]["message"]["content"]

        # --- Save conversation ---
        now = datetime.now().isoformat()
        knowledge_base.add_message(chat_id=chat_id, message={"role": "user", "content": query, "time": now})
        knowledge_base.add_message(chat_id=chat_id,
                                   message={"role": "assistant", "content": fine_tuned_answer, "time": now})

        logger.info(f"Chat completed for chat_id={chat_id}")

        return {
            "message": messages,
            "chat_id": chat_id,
            "answer": fine_tuned_answer,
            "sources": sources_list,
            "knowledge_used": knowledge_list
        }

    except Exception as e:
        logger.exception("LLM chat failed")
        return JSONResponse(status_code=400, content={"error": str(e)})
