import io
import logging
from datetime import datetime

import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from app.constant import Constant
from app.container import knowledge_base, llm_client

logging.basicConfig(
    level=logging.INFO,  # or DEBUG for more detail
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/knowledge/bulk-upload")
async def bulk_upload_knowledge(file: UploadFile = File(...)):
    try:
        # Load CSV into DataFrame
        contents = await file.read()

        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        # Track insert results
        results = []

        for _, row in df.iterrows():
            try:
                query_text = (
                    f"السؤال: {row['question']}\n"
                    f"العنوان: {row['title']}\n"
                    f"الإجابة: {row['answer']}"
                )

                payload = {
                    "title": row.get('title', 'No Title'),
                    "question": row.get('question', 'No Question'),
                    "answer": row.get('answer', 'No Answer'),
                    "source": row.get('source', None),
                    "published_at": row.get('published_at', None),
                }
                # Add to knowledge base
                knowledge_base.add_knowledge(
                    query_text=query_text,
                    payload=payload
                )
                results.append({"title": row['title'], "status": "success"})
            except Exception as e:
                results.append({"title": row.get('title', 'Unknown'), "status": "failed", "error": str(e)})

        return {"message": "Processing completed.", "results": results}

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
async def chat_with_llm(query: str, temperature: float = 0.7, chat_id: str = None):
    try:
        logger.info(f"Chat started. Query: {query} | Chat ID: {chat_id}")

        messages = [{
            "role": "system",
            "content": Constant.SYSTEM_PROMPT
        }]

        if chat_id:
            history = knowledge_base.get_messages(chat_id)
            if history:
                messages.extend(history[-4:])
        else:
            chat_id = str(knowledge_base.add_chat())
            logger.info(f"New chat started with ID: {chat_id}")

        knowledge = knowledge_base.get_knowledge(query_text=query, top_k=10, score_threshold=0.4)
        knowledge_list = [item.payload for item in knowledge] if knowledge else []

        user_query = {
            "role": "user",
            "content": f"##Knowledge: {knowledge_list}\n\n##User Query: {query}"
        }
        messages.append(user_query)

        response = llm_client.chat(messages=messages, temperature=temperature)
        answer = response["choices"][0]["message"]["content"]

        now = datetime.now().isoformat()
        knowledge_base.add_message(chat_id=chat_id, message={"role": "user", "content": query, "time": now})
        knowledge_base.add_message(chat_id=chat_id, message={"role": "assistant", "content": answer, "time": now})

        logger.info(f"Chat completed for chat_id={chat_id}")
        return {"chat_id": chat_id, "answer": answer}

    except Exception as e:
        logger.exception("LLM chat failed")
        return JSONResponse(status_code=400, content={"error": str(e)})
