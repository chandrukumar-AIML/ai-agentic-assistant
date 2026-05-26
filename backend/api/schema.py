from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    status:          str
    openai_healthy:  bool
    ollama_healthy:  bool
    neo4j_healthy:   bool
    redis_healthy:   bool
    circuit_state:   str


class IngestResponse(BaseModel):
    status:         str
    chunks_indexed: int
    filename:       str
    category:       str


class MessageRecord(BaseModel):
    role:    str
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages:   list[MessageRecord]
    count:      int


class RAGStatsResponse(BaseModel):
    faiss_vectors:     int
    chroma_documents:  int


class FeedbackRequest(BaseModel):
    run_id:  str
    score:   float = Field(..., ge=0.0, le=1.0)
    comment: str = ""


class FeedbackResponse(BaseModel):
    submitted: bool
    run_id:    str


class IngestURLRequest(BaseModel):
    url:      str
    category: str = "general"


class WSIncomingMessage(BaseModel):
    type:       str = "text"          # "text" | "vision" | "ping"
    content:    str = Field("", max_length=10000)
    session_id: Optional[str] = None
    image:      Optional[str] = None  # base64-encoded image data