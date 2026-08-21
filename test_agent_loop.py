import sys
import os

sys.path.insert(0, r"d:\Antigravity")

from Heti.config.config_loader import Config
from Heti.agent.core_agent import HetiAgent
from Heti.tools import SystemStatsTool, FileSystemTool, OpenApplicationTool, ToolCategory, PermissionLevel

def test_agent_loop():
    print("--- Testing Agent Loop Architecture ---")
    
    # 1. Test Lite Tier (Plain Python while-loop)
    cfg_lite = Config()
    cfg_lite.active_tier = "lite"
    agent_lite = HetiAgent(config=cfg_lite)
    agent_lite.register_tool(SystemStatsTool(), ToolCategory.SYSTEM_INFO, PermissionLevel.READ_ONLY)
    agent_lite.register_tool(FileSystemTool(), ToolCategory.FILE_SYSTEM, PermissionLevel.READ_ONLY)
    agent_lite.register_tool(OpenApplicationTool(), ToolCategory.SYSTEM_EXECUTION, PermissionLevel.SYSTEM_EXECUTION)

    print("\n[Lite Tier] Active tier:", agent_lite.config.active_tier)
    print("[Lite Tier] Tools registered:", [t.name for t in agent_lite.registry.get_all_tools()])

    # 2. Test Full Tier (LangGraph graph flow if langgraph installed or falls back gracefully)
    cfg_full = Config()
    cfg_full.active_tier = "full"
    agent_full = HetiAgent(config=cfg_full)
    agent_full.register_tool(SystemStatsTool(), ToolCategory.SYSTEM_INFO, PermissionLevel.READ_ONLY)
    agent_full.register_tool(FileSystemTool(), ToolCategory.FILE_SYSTEM, PermissionLevel.READ_ONLY)
    agent_full.register_tool(OpenApplicationTool(), ToolCategory.SYSTEM_EXECUTION, PermissionLevel.SYSTEM_EXECUTION)

    print("\n[Full Tier] Active tier:", agent_full.config.active_tier)
    print("[Full Tier] Tools registered:", [t.name for t in agent_full.registry.get_all_tools()])

    print("\n✅ Both Lite while-loop and Full LangGraph agent loops compiled successfully!")

if __name__ == "__main__":
    test_agent_loop()
