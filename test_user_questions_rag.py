import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, r"d:\Antigravity")

from Heti.config import Config
from Heti.rag import LocalRAGStore, RAGRetrievalHook

def run_rag_question_benchmark():
    print("=================================================================")
    print(" 🧪 RUNNING REAL USER QUESTIONS RAG EMBEDDING ROBUSTNESS BENCHMARK")
    print("=================================================================")

    kb_dir = Path("d:/Antigravity/Heti/trusted_kb").resolve()
    kb_file = kb_dir / "user_notes_kb.txt"
    test_db = Path("d:/Antigravity/Heti/test_rag_user_db").resolve()

    # Paired test questions (Technical Phrasing vs. Casual Phrasing)
    question_pairs = [
        {
            "topic": "REHS Bypass Valve",
            "technical": "What's the working principle of the REHS bypass valve?",
            "casual": "How does the REHS valve bypass work when it gets too hot or pressurized?"
        },
        {
            "topic": "IoT Flood Project Cost",
            "technical": "Summarize the last IoT flood project's cost breakdown",
            "casual": "How much money did we spend on the flood monitoring project and what were the expenses?"
        },
        {
            "topic": "Ekam Rate Limiting",
            "technical": "What did I write about Ekam's rate limiting?",
            "casual": "What are the rules and request limits for Ekam API and sockets before getting blocked?"
        }
    ]

    benchmark_results = []

    try:
        for tier in ["full", "lite"]:
            print(f"\n >>> BENCHMARKING TIER: {tier.upper()} <<<")
            config = Config()
            config.active_tier = tier

            rag_store = LocalRAGStore(
                persist_directory=str(test_db / f"chroma_{tier}"),
                embedding_model_name=config.embedding_model,
                persist_mode=config.rag_persist_mode,
                trusted_subfolder="trusted_kb"
            )

            # Ingest user notes document
            ingest_res = rag_store.ingest_file(str(kb_file), max_chunk_tokens=config.rag_chunk_size)
            print(f" 📥 Ingested KB Document ({ingest_res['chunks_ingested']} chunks)")

            hook = RAGRetrievalHook(rag_store=rag_store, config=config)

            for pair in question_pairs:
                topic = pair["topic"]

                # 1. Technical Query Retrieval
                aug_tech = hook.augment_query(pair["technical"], top_k=config.rag_top_k, summarize=config.rag_summarize_retrieved)
                tech_match = any(topic.split()[0].lower() in str(c["content"]).lower() for c in aug_tech.get("raw_chunks", []))

                # 2. Casual Query Retrieval
                aug_cas = hook.augment_query(pair["casual"], top_k=config.rag_top_k, summarize=config.rag_summarize_retrieved)
                cas_match = any(topic.split()[0].lower() in str(c["content"]).lower() for c in aug_cas.get("raw_chunks", []))

                benchmark_results.append({
                    "tier": tier,
                    "topic": topic,
                    "tech_query": pair["technical"],
                    "tech_success": tech_match,
                    "casual_query": pair["casual"],
                    "casual_success": cas_match
                })

                print(f" 📌 Topic: {topic}")
                print(f"    • Tech Query Match   : {'✅ SUCCESS' if tech_match else '❌ FAILED'}")
                print(f"    • Casual Query Match : {'✅ SUCCESS' if cas_match else '❌ FAILED'}")

    finally:
        if test_db.exists():
            shutil.rmtree(test_db)

    print("\n=================================================================")
    print(" ✅ USER RAG BENCHMARK COMPLETED SUCCESSFULLY")
    print("=================================================================")

if __name__ == "__main__":
    run_rag_question_benchmark()
