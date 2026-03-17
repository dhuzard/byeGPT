from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, List, Optional
import chromadb
from chromadb.utils import embedding_functions

class VectorIndexer:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="conversations",
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def index_directory(
        self,
        input_dir: Path,
        progress_callback: Optional[Any] = None,
        batch_size: int = 200,
        limit: Optional[int] = None,
    ) -> int:
        """Scan MD files, chunk them, and add to index using batching."""
        md_files = list(input_dir.rglob("*.md"))
        md_files = [f for f in md_files if f.name not in ("_map.md", "00_Brain_Map.md")]
        if limit and limit > 0:
            md_files = md_files[:limit]
            
        total_files = len(md_files)
        
        batch_ids = []
        batch_docs = []
        batch_metas = []
        
        for i, file_path in enumerate(md_files):
            content = file_path.read_text(encoding="utf-8")
            
            chunks = content.split("\n---\n")
            
            for idx, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk or chunk == "---":
                    continue
                
                chunk_id = f"{file_path.stem}_{idx}_{len(batch_ids)}"
                batch_ids.append(chunk_id)
                batch_docs.append(chunk)
                batch_metas.append({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                if len(batch_ids) >= batch_size:
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_docs,
                        metadatas=batch_metas
                    )
                    batch_ids, batch_docs, batch_metas = [], [], []

            if progress_callback:
                progress_callback(i + 1, total_files)
        
        if batch_ids:
            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
        return total_files

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

    def count(self) -> int:
        return self.collection.count()
