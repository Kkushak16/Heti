import sys
import os
import json

sys.path.insert(0, r"d:\Antigravity")

from Heti.config.config_loader import Config
from Heti.agent.core_agent import HetiAgent
from Heti.tools import SystemStatsTool, FileSystemTool, OpenApplicationTool, ToolCategory, PermissionLevel
from Heti.tools.registry import SecureToolRegistry

AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")

def auto_hitl_callback(tool_name: str, args: dict) -> bool:
    print(f"🤖 [Auto HITL Test Agent] Approving execution of '{tool_name}' with args {args}")
    return True

def run_end_to_end_test():
    if os.path.exists(AUDIT_LOG_FILE):
        os.remove(AUDIT_LOG_FILE)

    print("==================================================")
    print(" HETI AGENT END-TO-END LOOP & AUDIT LOGGING TEST")
    print("==================================================")

    # 1. Setup Registry with 3 tools & Auto HITL Callback
    cfg = Config()
    registry = SecureToolRegistry(
        permissions_config=cfg.permissions_config,
        hitl_callback=auto_hitl_callback,
        audit_log_path=AUDIT_LOG_FILE
    )

    t1 = SystemStatsTool()
    t2 = FileSystemTool()
    t3 = OpenApplicationTool()

    registry.register_tool(t1, ToolCategory.SYSTEM_INFO, PermissionLevel.READ_ONLY)
    registry.register_tool(t2, ToolCategory.FILE_SYSTEM, PermissionLevel.READ_ONLY)
    registry.register_tool(t3, ToolCategory.SYSTEM_EXECUTION, PermissionLevel.SYSTEM_EXECUTION)

    # 2. Test Lite Tier Tool Invocation Loop
    print("\n--- Testing Lite Tier (Plain Python while-loop) ---")
    cfg_lite = Config()
    cfg_lite.active_tier = "lite"
    agent_lite = HetiAgent(config=cfg_lite, registry=registry)

    print("Simulating Lite Tier tool execution sequence...")
    res_lite_1 = agent_lite.registry.execute_tool("get_system_stats", {"detailed": True})
    print(" ➔ get_system_stats output:", res_lite_1)

    res_lite_2 = agent_lite.registry.execute_tool("list_directory", {"directory_path": "."})
    print(" ➔ list_directory output:", res_lite_2)

    res_lite_3 = agent_lite.registry.execute_tool("open_application", {"app_name": "notepad"})
    print(" ➔ open_application output:", res_lite_3)

    # 3. Test Full Tier Tool Invocation Loop
    print("\n--- Testing Full Tier (LangGraph / State Architecture) ---")
    cfg_full = Config()
    cfg_full.active_tier = "full"
    agent_full = HetiAgent(config=cfg_full, registry=registry)

    print("Simulating Full Tier tool execution sequence...")
    res_full_1 = agent_full.registry.execute_tool("get_system_stats", {"detailed": False})
    print(" ➔ get_system_stats output:", res_full_1)

    res_full_2 = agent_full.registry.execute_tool("open_application", {"app_name": "calculator"})
    print(" ➔ open_application output:", res_full_2)

    # 4. Verify Local Audit Log
    print("\n==================================================")
    print(" VERIFYING AUDIT LOG FILE:", AUDIT_LOG_FILE)
    print("==================================================")

    if not os.path.exists(AUDIT_LOG_FILE):
        print("❌ Audit log file was NOT created!")
        return

    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        log_lines = f.readlines()

    print(f"Total audit log entries recorded: {len(log_lines)}\n")
    for idx, line in enumerate(log_lines, 1):
        data = json.loads(line.strip())
        print(f"Entry {idx}: [{data['timestamp']}] Tool: '{data['tool_name']}' | Status: {data['status']} | Category: {data['category']}")

    print("\n✅ End-to-end loop and structured local audit logging test complete!")

if __name__ == "__main__":
    run_end_to_end_test()
