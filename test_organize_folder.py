import sys
import os
import shutil

sys.path.insert(0, r"d:\Antigravity")

from Heti.tools import OrganizeFolderTool

def test_organize_folder_sandboxing():
    sandbox_dir = os.path.abspath("test_sandbox")
    os.makedirs(sandbox_dir, exist_ok=True)

    try:
        # Create test files inside sandbox
        with open(os.path.join(sandbox_dir, "doc1.pdf"), "w") as f: f.write("test")
        with open(os.path.join(sandbox_dir, "img1.png"), "w") as f: f.write("test")
        with open(os.path.join(sandbox_dir, "script.py"), "w") as f: f.write("print('hello')")
        with open(os.path.join(sandbox_dir, "archive.zip"), "w") as f: f.write("zip")
        with open(os.path.join(sandbox_dir, "unknown.xyz"), "w") as f: f.write("data")

        tool = OrganizeFolderTool(base_sandbox_dir=sandbox_dir)

        print("--- Testing Valid In-Sandbox Folder Organization ---")
        res = tool.execute(sandbox_dir)
        print("Result status:", res.get("status"))
        print("Files organized:", res.get("files_organized"))
        print("Details:", res.get("details"))

        print("\n--- Testing Path-Traversal Guard (`../`) ---")
        traversal_path = os.path.join(sandbox_dir, "..", "..", "Windows")
        res_guard = tool.execute(traversal_path)
        print("Path-traversal Block Result:", res_guard)

        print("\n--- Testing Absolute Path-Traversal Block (`C:\\Windows`) ---")
        res_abs_guard = tool.execute(r"C:\Windows")
        print("Absolute Path Block Result:", res_abs_guard)

        print("\n✅ OrganizeFolderTool path-traversal guard & sandboxing verified!")

    finally:
        if os.path.exists(sandbox_dir):
            shutil.rmtree(sandbox_dir)

if __name__ == "__main__":
    test_organize_folder_sandboxing()
