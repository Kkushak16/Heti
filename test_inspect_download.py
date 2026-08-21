import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, r"d:\Antigravity")

from Heti.tools import InspectDownloadedFileTool

def test_inspect_downloaded_file():
    sandbox_dir = Path("test_inspect_sandbox").resolve()
    sandbox_dir.mkdir(exist_ok=True)

    dummy_exe = sandbox_dir / "sample_installer.exe"
    dummy_exe.write_bytes(b"MZ_DUMMY_BINARY_DATA_HEADER_PE_EXEC_TEST")

    try:
        tool = InspectDownloadedFileTool(base_sandbox_dir=str(sandbox_dir))

        print("--- Testing InspectDownloadedFileTool ---")
        res = tool.execute("sample_installer.exe")
        print("Inspection Results:")
        print(res)

        assert res.get("status") == "success", "Inspection failed!"
        assert "hashes" in res and "sha256" in res["hashes"] and "md5" in res["hashes"], "Missing hashes!"
        assert res.get("auto_execution_prevented") is True, "Auto execution safety flag missing!"
        assert "digital_signature" in res, "Digital signature check missing!"

        print("\n✅ InspectDownloadedFileTool verified safely (no auto-execution, hashes & signature checked)!")

    finally:
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir)

if __name__ == "__main__":
    test_inspect_downloaded_file()
