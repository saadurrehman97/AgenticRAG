"""Configuration management for the RAG system."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    """System configuration."""

    # API Keys
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    # Model settings
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4-turbo-preview"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))

    # Chunking settings
    chunk_size: int = Field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "500")))
    chunk_overlap: int = Field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "50")))

    # Graph settings
    max_graph_hops: int = Field(default_factory=lambda: int(os.getenv("MAX_GRAPH_HOPS", "3")))
    min_entity_freq: int = 2
    similarity_threshold: float = 0.7

    # Paths
    data_dir: str = "data"
    graph_dir: str = "graph"

    class Config:
        arbitrary_types_allowed = True


config = Config()
