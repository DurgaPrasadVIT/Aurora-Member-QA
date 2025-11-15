import logging

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .services.messages import AuroraMessagesClient
from .extractors import build_documents
from .qa import QASystem


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aurora_app")


class Question(BaseModel):
    question: str


class QAResponse(BaseModel):
    answer: str


app = FastAPI(title="Aurora Member QA", version="0.3.0")

qa_system = QASystem()
messages_client = AuroraMessagesClient()


@app.on_event("startup")
async def startup_event() -> None:
    """
    On startup:
    1. Fetch messages from Aurora API
    2. Build plain-text documents
    3. Build TF-IDF index over those documents
    """
    try:
        logger.info("Fetching messages from Aurora API...")
        messages = await messages_client.get_messages()
        logger.info("Fetched %d raw messages.", len(messages))

        docs = build_documents(messages)
        logger.info("Built %d documents for QA index.", len(docs))

        qa_system.build(docs)
        logger.info("Startup complete: QA index ready.")
    except Exception as exc:
        logger.exception("Failed during startup: %s", exc)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=QAResponse)
async def ask(payload: Question) -> QAResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    answer = qa_system.answer(question)
    return QAResponse(answer=answer)


@app.get("/ask", response_model=QAResponse)
async def ask_get(
    question: str = Query(..., min_length=1, description="Natural-language question"),
) -> QAResponse:
    """
    GET version of /ask to match the example in the assignment:

        GET /ask?question=When%20is%20Layla... 

    Returns the same response format as POST /ask.
    """
    answer = qa_system.answer(question)
    return QAResponse(answer=answer)
