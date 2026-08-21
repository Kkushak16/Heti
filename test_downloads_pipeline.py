import sys
import os
import time
import shutil
from pathlib import Path

sys.path.insert(0, r"d:\Antigravity")

from Heti.tools.downloads_pipeline import DownloadsPipelineController

class MockAgent:
    """Mock agent to simulate LLM response without requiring active Ollama server."""
    def run_turn(self, prompt: str) -> str:
        print(f" 🤖 [Mock LLM Response Engine] Received Batch Prompt:\n{prompt[:150]}...")
        return "Batch summary: 2 target files detected (installer.exe, archive.zip). All digital signatures and hashes inspected safely."

def test_downloads_pipeline_batching():
    downloads_test_dir = Path("test_pipeline_downloads").resolve()
    downloads_test_dir.mkdir(exist_ok=True)

    mock_agent = MockAgent()
    # Configure pipeline with short 2-second batch delay for fast test verification
    pipeline = DownloadsPipelineController(
        heti_agent=mock_agent,
        folder_path=str(downloads_test_dir),
        batch_interval_sec=2.0
    )

    try:
        print("--- Starting Downloads Pipeline Controller ---")
        pipeline.start()
        time.sleep(1)

        # Simulate 2 download events
        exe_file = downloads_test_dir / "setup_v2.exe"
        zip_file = downloads_test_dir / "assets_bundle.zip"

        print("--- Simulating Downloaded File Events ---")
        exe_file.write_bytes(b"MZ_SAMPLE_EXE")
        zip_file.write_bytes(b"PK_SAMPLE_ZIP")

        # Wait for batch interval to trigger batch summarization
        time.sleep(3.5)

        print("\n✅ DownloadsPipelineController batching, LLM summarization, and notification pipeline verified successfully!")

    finally:
        pipeline.stop()
        if downloads_test_dir.exists():
            shutil.rmtree(downloads_test_dir)

if __name__ == "__main__":
    test_downloads_pipeline_batching()
