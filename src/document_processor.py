"""Document ingestion and chunking pipeline."""

import os
import re
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


@dataclass
class Chunk:
    """Represents a document chunk."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: str = ""
    embedding: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for chunk."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        source = self.metadata.get("source", "unknown")
        return f"{source}_{content_hash[:8]}"


class DocumentProcessor:
    """Handles document loading, parsing, and chunking."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def load_documents(self, data_dir: str) -> List[Document]:
        """Load all markdown and text files from data directory."""
        documents = []
        data_path = Path(data_dir)

        if not data_path.exists():
            raise ValueError(f"Data directory not found: {data_dir}")

        for file_path in data_path.glob("**/*"):
            if file_path.suffix.lower() in [".md", ".txt"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Extract metadata from content
                    metadata = self._extract_metadata(content, str(file_path))

                    documents.append(
                        Document(
                            page_content=content,
                            metadata=metadata,
                        )
                    )
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")

        return documents

    def _extract_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document content."""
        metadata = {
            "source": os.path.basename(file_path),
            "file_path": file_path,
        }

        # Try to extract title from markdown header or first line
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        else:
            # Use filename as title
            metadata["title"] = Path(file_path).stem.replace("_", " ").title()

        # Extract tags if present (e.g., tags: tag1, tag2)
        tags_match = re.search(r"tags:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if tags_match:
            tags = [tag.strip() for tag in tags_match.group(1).split(",")]
            metadata["tags"] = tags

        return metadata

    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """Split documents into chunks."""
        chunks = []

        for doc in documents:
            # Split the document
            splits = self.text_splitter.split_text(doc.page_content)

            for i, split_content in enumerate(splits):
                chunk_metadata = {
                    **doc.metadata,
                    "chunk_index": i,
                    "total_chunks": len(splits),
                }

                chunk = Chunk(
                    content=split_content,
                    metadata=chunk_metadata,
                )
                chunks.append(chunk)

        return chunks

    def process(self, data_dir: str) -> List[Chunk]:
        """Complete processing pipeline: load and chunk documents."""
        documents = self.load_documents(data_dir)
        chunks = self.chunk_documents(documents)
        return chunks
