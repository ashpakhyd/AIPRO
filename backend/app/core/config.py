from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    log_level: str = "INFO"
    upload_dir: str = "./uploads"
    data_dir: str = "./data"
    max_upload_size_mb: int = 50
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "knowledge_base"

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # LLM
    llm_provider: str = "huggingface_local"
    llm_model_id: str = "microsoft/phi-2"
    llm_device: str = "cpu"
    llm_max_new_tokens: int = 512
    llm_temperature: float = 0.1

    # HuggingFace API
    huggingface_api_key: str = ""
    hf_inference_model: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # OpenAI-compatible
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"

    # RAG
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.3
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64

    # Agent
    agent_max_iterations: int = 5
    agent_timeout_seconds: int = 120

    # Web search
    serpapi_key: str = ""
    web_search_enabled: bool = False

    # News feature
    news_api_key: str = ""
    news_fetch_interval_minutes: int = 60

    # Fine-tuning
    finetune_base_model: str = "facebook/opt-125m"
    finetune_output_dir: str = "./training/output"
    finetune_dataset: str = "./training/datasets/sample_dataset.jsonl"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
