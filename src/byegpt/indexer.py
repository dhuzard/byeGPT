from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional
import datetime

import chromadb
from chromadb.utils import embedding_functions
from rich.console import Console

console = Console()

class VectorIndexer:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Use a simpler embedding initialization to bypass metadata issues
        self.client = chromadb.PersistentClient(path=str(db_path))
        
        # Use Chroma's default embedding function which is more resilient
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="conversations",
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"}
        )
        print("DEBUG: Collection ready")

    def index_directory(self, input_dir: Path, progress_callback: Optional[Any] = None):
        """Scan MD files, chunk them, and add to index."""
        md_files = list(input_dir.rglob("*.md"))
        # Exclude map files
        md_files = [f for f in md_files if f.name not in ("_map.md", "00_Brain_Map.md")]
        
        total_files = len(md_files)
        for i, file_path in enumerate(md_files):
            content = file_path.read_text(encoding="utf-8")
            self._index_file(file_path, content)
            
            if progress_callback:
                progress_callback(i + 1, total_files)

    def _index_file(self, file_path: Path, content: str):
        """Split file into conversation chunks and index each."""
        # Simple chunking by the '---' separator we use in formatter.py
        # Each '---' separates a full conversation in the big files
        chunks = content.split("\n---\n")
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk or chunk == "---":
                continue
            
            chunk_id = f"{file_path.stem}_{idx}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "source": str(file_path),
                "filename": file_path.name,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

    def query(self, text: str, n_results: int = 5) -> List[dict[str, Any]]:
        """Search for relevant chunks."""
        results = self.collection.query(
            query_texts=[text],
            n_results=n_results
        )
        
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        return formatted_results
