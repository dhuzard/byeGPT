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

    def index_directory(self, input_dir: Path, progress_callback: Optional[Any] = None, batch_size: int = 200, limit: Optional[int] = None):
        """Scan MD files, chunk them, and add to index using batching."""
        md_files = list(input_dir.rglob("*.md"))
        # Exclude map files
        md_files = [f for f in md_files if f.name not in ("_map.md", "00_Brain_Map.md")]
        
        # Apply limit if provided
        if limit and limit > 0:
            md_files = md_files[:limit]
            
        total_files = len(md_files)
        
        batch_ids = []
        batch_docs = []
        batch_metas = []
        
        for i, file_path in enumerate(md_files):
            content = file_path.read_text(encoding="utf-8")
            
            # Split file into conversation chunks
            chunks = content.split("\n---\n")
            
            for idx, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk or chunk == "---":
                    continue
                
                chunk_id = f"{file_path.stem}_{idx}_{len(batch_ids)}" # Add len to avoid collisions in same batch
                batch_ids.append(chunk_id)
                batch_docs.append(chunk)
                batch_metas.append({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                # If batch is full, add to collection
                if len(batch_ids) >= batch_size:
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_docs,
                        metadatas=batch_metas
                    )
                    batch_ids, batch_docs, batch_metas = [], [], []

            if progress_callback:
                progress_callback(i + 1, total_files)
        
        # Final flush
        if batch_ids:
            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
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
