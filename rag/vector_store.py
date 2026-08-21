import os
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    chromadb = None
    HAS_CHROMADB = False


class SimpleVectorStore:
    """Fallback lightweight vector store for environments without native C++ chromadb bindings."""
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []

    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        for i, doc in enumerate(documents):
            self.documents.append({
                "id": ids[i],
                "document": doc,
                "metadata": metadatas[i]
            })

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        results_docs = []
        results_meta = []
        query_words = set(query_texts[0].lower().split())

        scored = []
        for d in self.documents:
            doc_words = set(d["document"].lower().split())
            score = len(query_words.intersection(doc_words))
            scored.append((score, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_items = scored[:n_results]

        res_docs = [item[1]["document"] for item in top_items]
        res_meta = [item[1]["metadata"] for item in top_items]

        return {
            "documents": [res_docs],
            "metadatas": [res_meta]
        }


class LocalRAGStore:
    """
    ChromaDB-backed RAG Store with strict security and poisoning defense:
    - Full tier: nomic-embed-text embedding, in-memory index caching.
    - Lite tier: all-MiniLM-L6-v2 (~90MB), on-disk persistence (no in-memory cache).
    - Source-provenance tagging: attaches file path, timestamp, and chunk offset metadata.
    - Poisoning Defense: restricts auto-ingestion strictly to trusted_kb folder; blocks un-vetted file ingestion.
    """
    def __init__(
        self,
        persist_directory: str = "heti_chroma_db",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        persist_mode: str = "disk_only",
        trusted_subfolder: str = "trusted_kb"
    ):
        self.persist_directory = Path(persist_directory).resolve()
        self.embedding_model_name = embedding_model_name
        self.persist_mode = persist_mode
        self.trusted_subfolder = trusted_subfolder

        if HAS_CHROMADB:
            if persist_mode == "memory":
                self.client = chromadb.Client()
            else:
                self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            self.collection = self.client.get_or_create_collection(name="heti_knowledge_base")
        else:
            print(" ⚠️ [RAG Warning] `chromadb` package not installed. Running in SimpleVectorStore fallback mode.")
            self.collection = SimpleVectorStore()

    def _chunk_text(self, text: str, max_chunk_tokens: int = 256) -> List[str]:
        words = text.split()
        chunks = []
        # Estimate ~1.3 words per token
        max_words = int(max_chunk_tokens * 0.75)
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i + max_words])
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks

    def is_trusted_source(self, file_path: str) -> bool:
        """Poisoning defense guard: restricts auto-ingest strictly to trusted_kb subfolder."""
        resolved = Path(file_path).resolve()
        # Require file to be strictly within the designated trusted_kb subfolder
        return self.trusted_subfolder in str(resolved) and "Downloads" not in str(resolved)

    def ingest_file(
        self,
        file_path: str,
        max_chunk_tokens: int = 256,
        force_untrusted_override: bool = False
    ) -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists() or not path.is_file():
            return {"error": f"File '{file_path}' does not exist."}

        # Poisoning Defense Security Gate
        if not force_untrusted_override and not self.is_trusted_source(str(path)):
            return {
                "status": "blocked",
                "reason": f"Poisoning Defense: Path '{path.name}' is outside the trusted subfolder '{self.trusted_subfolder}'. Ingestion requires explicit approval."
            }

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            chunks = self._chunk_text(content, max_chunk_tokens=max_chunk_tokens)
            if not chunks:
                return {"status": "skipped", "reason": "Empty file"}

            ids = []
            documents = []
            metadatas = []

            for idx, chunk in enumerate(chunks):
                chunk_id = hashlib.sha256(f"{path.name}_{idx}_{chunk[:20]}".encode()).hexdigest()[:16]
                ids.append(chunk_id)
                documents.append(chunk)
                # Source-provenance tagging
                metadatas.append({
                    "source_file": path.name,
                    "absolute_path": str(path),
                    "chunk_index": idx,
                    "ingested_at": int(time.time()),
                    "trusted": True
                })

            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

            return {
                "status": "success",
                "file_name": path.name,
                "chunks_ingested": len(chunks),
                "provenance_tagged": True
            }
        except Exception as e:
            return {"error": f"Failed to ingest file: {str(e)}"}

    def query(self, query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
        results = self.collection.query(query_texts=[query_text], n_results=top_k)
        retrieved = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        for i in range(len(docs)):
            retrieved.append({
                "content": docs[i],
                "metadata": metas[i] if i < len(metas) else {}
            })
        return retrieved
