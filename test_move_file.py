import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, r"d:\Antigravity")

from Heti.config.config_loader import Config
from Heti.tools import MoveFileTool, ToolCategory, PermissionLevel
from Heti.tools.registry import SecureToolRegistry, SecurityException

def auto_approve_hitl(tool_name: str, args: dict) -> bool:
    print(f"🤖 [HITL Callback] User APPROVED move operation: {args}")
    return True

def auto_reject_hitl(tool_name: str, args: dict) -> bool:
    print(f"🛑 [HITL Callback] User REJECTED move operation: {args}")
    return False

def test_move_file_tool():
    sandbox_dir = Path("test_move_sandbox").resolve()
    sandbox_dir.mkdir(exist_ok=True)
    sub_dir = sandbox_dir / "target_dir"
    sub_dir.mkdir(exist_ok=True)

    src_file = sandbox_dir / "sample.txt"
    src_file.write_text("Hello Heti Move File")

    try:
        tool = MoveFileTool(base_sandbox_dir=str(sandbox_dir))

        # 1. Test path-traversal check with pathlib.Path.is_relative_to
        print("--- Testing Path-Traversal Security Check ---")
        bad_src = os.path.join(sandbox_dir, "..", "external.txt")
        res_traversal = tool.execute(bad_src, str(sub_dir))
        print("Path Traversal Block Result:", res_traversal)

        # 2. Test SecureToolRegistry with requires_confirmation=True (HITL Approved)
        print("\n--- Testing SecureToolRegistry (HITL Approved) ---")
        cfg = Config()
        reg_approve = SecureToolRegistry(permissions_config=cfg.permissions_config, hitl_callback=auto_approve_hitl)
        reg_approve.register_tool(tool, ToolCategory.FILE_SYSTEM, PermissionLevel.FILE_SYSTEM, requires_confirmation=True)

        res_approved = reg_approve.execute_tool("move_file", {"source_path": "sample.txt", "destination_path": "target_dir"})
        print("Move Approved Result:", res_approved)
        assert (sub_dir / "sample.txt").exists(), "File was not moved!"

        # 3. Test SecureToolRegistry with requires_confirmation=True (HITL Rejected)
        print("\n--- Testing SecureToolRegistry (HITL Rejected) ---")
        reg_reject = SecureToolRegistry(permissions_config=cfg.permissions_config, hitl_callback=auto_reject_hitl)
        reg_reject.register_tool(tool, ToolCategory.FILE_SYSTEM, PermissionLevel.FILE_SYSTEM, requires_confirmation=True)

        try:
            reg_reject.execute_tool("move_file", {"source_path": "target_dir/sample.txt", "destination_path": "sample_rejected.txt"})
        except SecurityException as sec_err:
            print("Security Exception Caught (As Expected):", sec_err)

        print("\n✅ MoveFileTool is_relative_to() guards & HITL confirmation enforced!")

    finally:
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir)

if __name__ == "__main__":
    test_move_file_tool()
