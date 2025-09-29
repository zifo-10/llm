import json
import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.constant import Constant
from app.container import knowledge_base, llm_client

# Token management constants
MAX_CONTEXT_TOKENS = 3500  # Leave buffer for completion tokens
MAX_COMPLETION_TOKENS = 800
TOKEN_OVERHEAD = 200  # Buffer for system prompts and formatting

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


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))


def estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 characters per token for English, ~2 for Arabic."""
    # Simple heuristic: count words and characters
    words = len(text.split())
    chars = len(text)
    
    # Arabic text typically has fewer tokens per character
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    non_arabic_chars = chars - arabic_chars
    
    # Rough estimation: Arabic ~2 chars/token, others ~4 chars/token
    estimated_tokens = (arabic_chars / 2) + (non_arabic_chars / 4)
    
    # Add some buffer for punctuation and formatting
    return int(estimated_tokens * 1.1)


def truncate_knowledge_to_fit(knowledge_list: List[dict], max_tokens: int) -> List[dict]:
    """Truncate knowledge list to fit within token limit."""
    if not knowledge_list:
        return knowledge_list
    
    truncated = []
    current_tokens = 0
    
    for item in knowledge_list:
        item_text = str(item)
        item_tokens = estimate_tokens(item_text)
        
        if current_tokens + item_tokens <= max_tokens:
            truncated.append(item)
            current_tokens += item_tokens
        else:
            # Try to fit a truncated version of this item
            remaining_tokens = max_tokens - current_tokens
            if remaining_tokens > 50:  # Only if we have meaningful space left
                # Truncate the item content
                truncated_item = item.copy()
                if 'answer' in truncated_item:
                    # Truncate the answer field
                    answer = truncated_item['answer']
                    max_chars = remaining_tokens * 3  # Rough conversion back to chars
                    if len(answer) > max_chars:
                        truncated_item['answer'] = answer[:max_chars] + "..."
                truncated.append(truncated_item)
            break
    
    return truncated


def truncate_messages_to_fit(messages: List[dict], max_tokens: int) -> List[dict]:
    """Truncate message history to fit within token limit, keeping system prompt."""
    if not messages:
        return messages
    
    # Always keep the system prompt (first message)
    system_prompt = messages[0] if messages else None
    other_messages = messages[1:] if len(messages) > 1 else []
    
    if not other_messages:
        return messages
    
    # Calculate system prompt tokens
    system_tokens = estimate_tokens(system_prompt['content']) if system_prompt else 0
    available_tokens = max_tokens - system_tokens
    
    if available_tokens <= 0:
        return [system_prompt] if system_prompt else []
    
    # Keep messages from the end (most recent) until we hit the limit
    truncated = [system_prompt] if system_prompt else []
    current_tokens = 0
    
    for message in reversed(other_messages):
        message_tokens = estimate_tokens(message['content'])
        if current_tokens + message_tokens <= available_tokens:
            truncated.insert(1, message)  # Insert after system prompt
            current_tokens += message_tokens
        else:
            break
    
    return truncated


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
            "content": Constant.DRAFTER_PROMPT
        }]
        fine_tuned_messages = [{
            "role": "system",
            "content": Constant.VERIFIER_PROMPT
        }]

        search_query = query

        # Use history if available
        if chat_id:
            history = knowledge_base.get_messages(chat_id)
            if history:
                # Truncate history to fit within token limits
                max_history_tokens = MAX_CONTEXT_TOKENS - TOKEN_OVERHEAD - estimate_tokens(query)
                messages = truncate_messages_to_fit(messages + history, max_history_tokens)
                fine_tuned_messages = truncate_messages_to_fit(fine_tuned_messages + history, max_history_tokens)

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

        # --- Truncate knowledge to fit within token limits ---
        # Calculate available tokens for knowledge
        current_tokens = sum(estimate_tokens(msg['content']) for msg in messages)
        query_tokens = estimate_tokens(query)
        available_knowledge_tokens = MAX_CONTEXT_TOKENS - current_tokens - query_tokens - TOKEN_OVERHEAD
        
        if available_knowledge_tokens > 0:
            knowledge_list = truncate_knowledge_to_fit(knowledge_list, available_knowledge_tokens)
            logger.info(f"Truncated knowledge to fit {available_knowledge_tokens} tokens, using {len(knowledge_list)} items")
        else:
            logger.warning("No tokens available for knowledge, using empty knowledge list")
            knowledge_list = []

        # --- Final user query with retrieved knowledge ---
        user_query = {
            "role": "user",
            "content": f"##Knowledge: {knowledge_list}\n\n##User Query: {query}"
        }
        messages.append(user_query)

        # --- LLM call ---
        # Final token check before sending to LLM
        total_tokens = sum(estimate_tokens(msg['content']) for msg in messages)
        logger.info(f"Total context tokens: {total_tokens}/{MAX_CONTEXT_TOKENS}")
        if total_tokens > MAX_CONTEXT_TOKENS:
            logger.warning(f"Total tokens ({total_tokens}) exceed limit ({MAX_CONTEXT_TOKENS}), truncating further")
            messages = truncate_messages_to_fit(messages, MAX_CONTEXT_TOKENS - TOKEN_OVERHEAD)
            final_tokens = sum(estimate_tokens(msg['content']) for msg in messages)
            logger.info(f"After truncation: {final_tokens} tokens")
        
        response = llm_client.chat(messages=messages, temperature=temperature, max_tokens=MAX_COMPLETION_TOKENS)
        answer = response["choices"][0]["message"]["content"]

        # --- Check LLM response ---
        # Determine user language (simple heuristic)
        user_language = "ar" if any('\u0600' <= char <= '\u06FF' for char in query) else "en"
        
        # Format context blocks for verification
        context_blocks = [{"id": f"c{i}", "text": str(item)} for i, item in enumerate(knowledge_list)]
        
        # Create JSON payload for verification agent
        verification_payload = {
            "user_language": user_language,
            "user_message": query,
            "context_blocks": context_blocks,
            "draft_answer": answer
        }
        
        query_with_answer = {
            "role": "user",
            "content": json.dumps(verification_payload)
        }
        fine_tuned_messages.append(query_with_answer)
        
        # Final token check for verification
        verification_tokens = sum(estimate_tokens(msg['content']) for msg in fine_tuned_messages)
        logger.info(f"Verification context tokens: {verification_tokens}/{MAX_CONTEXT_TOKENS}")
        if verification_tokens > MAX_CONTEXT_TOKENS:
            logger.warning(f"Verification tokens ({verification_tokens}) exceed limit, truncating")
            fine_tuned_messages = truncate_messages_to_fit(fine_tuned_messages, MAX_CONTEXT_TOKENS - TOKEN_OVERHEAD)
            final_verification_tokens = sum(estimate_tokens(msg['content']) for msg in fine_tuned_messages)
            logger.info(f"After verification truncation: {final_verification_tokens} tokens")
        
        fine_tuned_llm = llm_client.chat(messages=fine_tuned_messages, temperature=0.1, max_tokens=MAX_COMPLETION_TOKENS)
        verification_response = fine_tuned_llm["choices"][0]["message"]["content"]
        
        # Parse JSON response from verification agent
        try:
            verification_result = json.loads(verification_response)
            fine_tuned_answer = verification_result["final_answer"]
            logger.info(f"Verification status: {verification_result.get('status', 'unknown')} - {verification_result.get('reason', 'no reason provided')}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse verification response: {e}. Using original answer.")
            fine_tuned_answer = answer

        # --- Save conversation ---
        now = datetime.now().isoformat()
        knowledge_base.add_message(chat_id=chat_id, message={"role": "user", "content": query, "time": now})
        knowledge_base.add_message(chat_id=chat_id, message={"role": "assistant", "content": fine_tuned_answer, "time": now})

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

