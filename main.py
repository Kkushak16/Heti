import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from Heti.config.safe_io import setup_safe_io, safe_print

setup_safe_io()



from Heti.config.config_loader import Config
from Heti.agent.core_agent import HetiAgent
from Heti.tools.system_tools import get_default_tools
from Heti.voice import FullVoiceLoopPipeline
from Heti.rag import LocalRAGStore, KnowledgeBaseWatcher, RAGRetrievalHook

def main():
    parser = argparse.ArgumentParser(description="Heti Voice & Text Local Agent Interface")
    parser.add_argument("--tier", choices=["full", "lite"], default=None, help="Set active model tier (full or lite)")
    parser.add_argument("--mode", choices=["interactive", "voice", "text"], default="interactive", help="Run mode: interactive (CLI), voice loop, or text query")
    parser.add_argument("--query", type=str, default=None, help="Single text query to run")
    args = parser.parse_args()

    config = Config()
    if args.tier:
        config.active_tier = args.tier

    print("=================================================================")
    print(f" 🤖 HETI LOCAL AGENT RUNTIME | ACTIVE TIER: {config.active_tier.upper()}")
    print("=================================================================")
    config.print_summary()

    # 1. Initialize RAG & Knowledge Base Watcher
    kb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "trusted_kb"))
    os.makedirs(kb_dir, exist_ok=True)

    rag_store = LocalRAGStore(
        persist_directory=os.path.abspath(os.path.join(os.path.dirname(__file__), f"chroma_{config.active_tier}")),
        embedding_model_name=config.embedding_model,
        persist_mode=config.rag_persist_mode,
        trusted_subfolder="trusted_kb"
    )

    kb_watcher = KnowledgeBaseWatcher(
        kb_folder=kb_dir,
        rag_store=rag_store,
        poll_interval_sec=5.0,
        max_chunk_tokens=config.rag_chunk_size
    )

    kb_watcher.start()

    # 2. Register Tools & Initialize Agent
    agent = HetiAgent(config=config)
    for tool in get_default_tools():
        agent.register_tool(tool)

    rag_hook = RAGRetrievalHook(rag_store=rag_store, agent=agent, config=config)
    voice_pipeline = FullVoiceLoopPipeline(agent=agent, config=config)

    # 3. Single Query Execution Mode
    if args.query:
        print(f"\n💬 Query: \"{args.query}\"")
        aug = rag_hook.augment_query(args.query, top_k=config.rag_top_k, summarize=config.rag_summarize_retrieved)
        prompt = aug["augmented_prompt"] if aug["rag_active"] else args.query
        response = agent.run_turn(prompt)
        print(f"\n🤖 Heti: {response}\n")
        kb_watcher.stop()
        return

    # 4. Voice Loop Mode
    if args.mode == "voice":
        print("\n🎙️ Starting Voice Loop (Wake word -> Record -> STT -> Agent -> TTS)...")
        print(" Say 'Hey Jarvis' or press Ctrl+C to exit.\n")
        try:
            voice_pipeline.run_voice_loop()
        except KeyboardInterrupt:
            print("\n Stopping voice loop.")
        finally:
            kb_watcher.stop()
        return

    # 5. Interactive CLI Chat Mode
    print("\n💬 Interactive CLI Mode Enabled. Type 'exit' to quit, or 'voice' to switch to wake-word mode.")
    print(" You can ask general questions, trigger OS tools, or query your notes in 'trusted_kb/'.\n")

    try:
        while True:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                break
            if user_input.lower() == "voice":
                print("\n🎙️ Switching to Voice Mode...")
                voice_pipeline.run_voice_loop()
                break

            # Check RAG augmentation
            aug = rag_hook.augment_query(user_input, top_k=config.rag_top_k, summarize=config.rag_summarize_retrieved)
            if aug["rag_active"]:
                print(f" 📚 [RAG Retrieved Sources: {', '.join(aug['sources'])}]")
                prompt = aug["augmented_prompt"]
            else:
                prompt = user_input

            response = agent.run_turn(prompt)
            print(f"\n🤖 Heti: {response}\n")

    except KeyboardInterrupt:
        print("\n Exiting Heti.")
    finally:
        kb_watcher.stop()

if __name__ == "__main__":
    main()
