import sys
import os
import time
from pathlib import Path

sys.path.insert(0, r"d:\Antigravity")

from Heti.tools import DownloadsFolderMonitor

def test_downloads_watchdog():
    downloads_test_dir = Path("test_downloads_dir").resolve()
    downloads_test_dir.mkdir(exist_ok=True)

    detected_events = []

    def handle_new_download(file_path: str, event_type: str):
        print(f" 🔥 [Callback Triggered] File: {file_path} | Event: {event_type}")
        detected_events.append((file_path, event_type))

    monitor = DownloadsFolderMonitor(folder_path=str(downloads_test_dir), callback=handle_new_download)

    try:
        print("--- Starting Downloads Monitor ---")
        monitor.start()
        time.sleep(1)

        # Create dummy target files (.exe, .msi, .zip)
        exe_file = downloads_test_dir / "installer.exe"
        msi_file = downloads_test_dir / "setup.msi"
        zip_file = downloads_test_dir / "archive.zip"
        txt_file = downloads_test_dir / "ignore.txt"

        print("--- Creating Test Files ---")
        exe_file.write_text("dummy exe")
        msi_file.write_text("dummy msi")
        zip_file.write_text("dummy zip")
        txt_file.write_text("dummy txt - should be ignored")

        time.sleep(3)

        print("\n--- Summary of Detected Events ---")
        print(f"Total target files detected: {len(detected_events)}")
        for path, evt in detected_events:
            print(f"- Path: {path} ({evt})")

        detected_filenames = [Path(p).name for p, _ in detected_events]
        assert "installer.exe" in detected_filenames, "Failed to detect .exe file!"
        assert "setup.msi" in detected_filenames, "Failed to detect .msi file!"
        assert "archive.zip" in detected_filenames, "Failed to detect archive file!"
        assert "ignore.txt" not in detected_filenames, ".txt file was not ignored!"

        print("\n✅ DownloadsFolderMonitor watchdog event detection verified successfully!")

    finally:
        monitor.stop()
        if downloads_test_dir.exists():
            import shutil
            shutil.rmtree(downloads_test_dir)

if __name__ == "__main__":
    test_downloads_watchdog()
