from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── Core LLM ──────────────────────────────────────────────────────────────
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_cost_per_1k_tokens: float = 0.0025

    # ── LangSmith ─────────────────────────────────────────────────────────────
    langchain_api_key: str
    langchain_tracing_v2: bool = True
    langchain_project: str = "ai-agentic-assistant"

    # ── RAG ───────────────────────────────────────────────────────────────────
    faiss_index_path: str = "./data/faiss_index"
    chroma_persist_path: str = "./data/chroma_db"
    chunk_size: int = 512
    chunk_overlap: int = 64
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # ── Web search ────────────────────────────────────────────────────────────
    tavily_api_key: str

    # ── Ollama (local LLM, used for A/B testing with open-source models) ──────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    postgres_host:     str = "localhost"
    postgres_port:     int = 5432
    postgres_db:       str = "agentic_v2"
    postgres_user:     str = "postgres"
    postgres_password: str = "postgres"      # override via POSTGRES_PASSWORD in .env
    database_url:      Optional[str] = None  # full DSN e.g. postgresql://user:pass@host/db

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Observability ─────────────────────────────────────────────────────────
    mlflow_tracking_uri: str = "/app/data/mlflow_runs"
    prometheus_port: int = 9090

    # ── API / Auth ────────────────────────────────────────────────────────────
    jwt_secret: str
    api_rate_limit: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Feature 6 — HITL notifications ───────────────────────────────────────
    sendgrid_api_key:      Optional[str] = None
    slack_webhook_url:     Optional[str] = None
    hitl_reviewer_email:   Optional[str] = None

    # ── Feature 5 / 13 — Twilio ──────────────────────────────────────────────
    twilio_account_sid:    Optional[str] = None
    twilio_auth_token:     Optional[str] = None
    twilio_phone_number:   Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None

    # ── Feature 5 — Calendly ─────────────────────────────────────────────────
    calendly_api_key:      Optional[str] = None

    # ── Feature 5 / 18 — DocuSign e-signature ────────────────────────────────
    docusign_integration_key: Optional[str] = None
    docusign_account_id:      Optional[str] = None
    docusign_base_url:        str = "https://demo.docusign.net/restapi"
    docusign_access_token:    Optional[str] = None

    # ── Feature 8 — Billing: Stripe + Razorpay ───────────────────────────────
    stripe_secret_key:        Optional[str] = None
    stripe_webhook_secret:    Optional[str] = None
    stripe_publishable_key:   Optional[str] = None
    razorpay_key_id:          Optional[str] = None
    razorpay_key_secret:      Optional[str] = None

    # ── Feature 9 — AgriTech ─────────────────────────────────────────────────
    openweather_api_key:      Optional[str] = None

    # ── Feature 10 — Indian Legal Research ───────────────────────────────────
    indiankanoon_api_key:     Optional[str] = None

    # ── Feature 15 — AI Email Manager (OAuth) ────────────────────────────────
    gmail_client_id:          Optional[str] = None
    gmail_client_secret:      Optional[str] = None
    gmail_redirect_uri:       str = "http://localhost:8000/api/email/oauth/gmail/callback"
    outlook_client_id:        Optional[str] = None
    outlook_client_secret:    Optional[str] = None
    outlook_tenant_id:        str = "common"

    # ── Feature 16 — AI Sales / CRM ──────────────────────────────────────────
    hubspot_api_key:          Optional[str] = None
    salesforce_instance_url:  Optional[str] = None
    salesforce_access_token:  Optional[str] = None
    clearbit_api_key:         Optional[str] = None

    # ── External services ─────────────────────────────────────────────────────
    playwright_service_url: Optional[str] = None   # PLAYWRIGHT_SERVICE_URL
    coqui_tts_url:          Optional[str] = None   # COQUI_TTS_URL
    mem0_api_key:           Optional[str] = None   # MEM0_API_KEY (cloud Mem0)

    # ── Feature Voice / TTS ───────────────────────────────────────────────────
    elevenlabs_api_key:           Optional[str] = None
    elevenlabs_voice_id:          Optional[str] = None

    # ── Feature 19 — AI Social Media Manager ─────────────────────────────────
    twitter_bearer_token:        Optional[str] = None
    twitter_api_key:             Optional[str] = None
    twitter_api_secret:          Optional[str] = None
    twitter_access_token:        Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    linkedin_author_urn:         Optional[str] = None   # urn:li:person:xxxx
    buffer_access_token:         Optional[str] = None

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v

    @field_validator("langchain_api_key")
    @classmethod
    def validate_langsmith_key(cls, v: str) -> str:
        if not (v.startswith("ls__") or v.startswith("lsv2_")):
            raise ValueError("LANGCHAIN_API_KEY must start with 'ls__' or 'lsv2_'")
        return v

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 chars. "
                "Generate with: openssl rand -hex 32"
            )
        return v

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings — reads .env once at startup."""
    return Settings()  # FIXED: removed loose module-level field stubs (lines 98-129) that were outside the Settings class and silently did nothing
