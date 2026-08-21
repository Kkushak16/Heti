import os
import time
import threading
from pathlib import Path
from typing import Callable, Optional

from Heti.rag.vector_store import LocalRAGStore


class KnowledgeBaseWatcher:
    """
    Auto-ingests new or modified files inside the designated trusted_kb folder.
    Poisoning Guard: Ignore untrusted files or outside folders.
    """
    def __init__(
        self,
        kb_folder: str,
        rag_store: LocalRAGStore,
        max_chunk_tokens: int = 256,
        poll_interval_sec: float = 2.0
    ):
        self.kb_folder = Path(kb_folder).resolve()
        self.rag_store = rag_store
        self.max_chunk_tokens = max_chunk_tokens
        self.poll_interval_sec = poll_interval_sec

        self.running = False
        self._thread = None
        self._file_mtimes = {}

    def start(self):
        if self.running:
            return
        self.running = True
        self.kb_folder.mkdir(parents=True, exist_ok=True)
        print(f" 📂 [KB Watcher] Started watching trusted folder: '{self.kb_folder}'")

        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def _watch_loop(self):
        while self.running:
            time.sleep(self.poll_interval_sec)
            self._scan_and_ingest()

    def _scan_and_ingest(self):
        if not self.kb_folder.exists():
            return

        for path in self.kb_folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in [".txt", ".md", ".json", ".csv", ".py"]:
                abs_str = str(path.resolve())
                try:
                    mtime = path.stat().st_mtime
                    if abs_str not in self._file_mtimes or self._file_mtimes[abs_str] < mtime:

                        print(f" 📄 [KB Watcher] Auto-ingesting new/updated file: {path.name}")
                        res = self.rag_store.ingest_file(
                            file_path=abs_str,
                            max_chunk_tokens=self.max_chunk_tokens
                        )
                        print(f" 📥 Ingestion Result: {res}")
                        self._file_mtimes[abs_str] = mtime
                except Exception as e:
                    print(f" ⚠️ [KB Watcher Error] {e}")

    def stop(self):
        self.running = False
        print(" 🛑 [KB Watcher] Stopped.")
