from typing import Dict, Any, List
from Heti.rag.vector_store import LocalRAGStore


class RAGRetrievalHook:
    """
    RAG Retrieval Hook for Heti Agent:
    - Performs top-k chunk retrieval prior to complex query answering.
    - Lite Tier: k=2-3 (vs k=5 in full), and summarizes retrieved chunks before feeding small LLMs to fit tight context windows.
    - Preserves source-provenance metadata (file name, path, chunk index).
    """
    def __init__(self, rag_store: LocalRAGStore, agent=None, config=None):
        self.rag_store = rag_store
        self.agent = agent
        self.config = config

    def _summarize_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Summarizes retrieved chunks before passing to small LLM context windows."""
        raw_text = "\n---\n".join([c["content"] for c in chunks])
        return raw_text[:300] + "..." if len(raw_text) > 300 else raw_text

    def augment_query(self, user_query: str, top_k: int = 2, summarize: bool = False) -> Dict[str, Any]:
        chunks = self.rag_store.query(query_text=user_query, top_k=top_k)
        if not chunks:
            return {
                "augmented_prompt": user_query,
                "sources": [],
                "rag_active": False
            }

        sources = []
        for c in chunks:
            meta = c.get("metadata", {})
            sources.append(f"{meta.get('source_file', 'unknown')} (chunk {meta.get('chunk_index', 0)})")

        if summarize:
            context_str = self._summarize_chunks(chunks)
        else:
            context_str = "\n".join([f"[{c['metadata'].get('source_file')}]: {c['content']}" for c in chunks])

        augmented_prompt = (
            f"[RETRIEVED KNOWLEDGE CONTEXT (Sources: {', '.join(sources)})]\n"
            f"{context_str}\n\n"
            f"[USER QUERY]\n"
            f"{user_query}"
        )

        return {
            "augmented_prompt": augmented_prompt,
            "sources": sources,
            "raw_chunks": chunks,
            "rag_active": True
        }
