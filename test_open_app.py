import sys
import os

# Add workspace directory to path
sys.path.insert(0, r"d:\Antigravity")

from Heti.tools import OpenApplicationTool, AllowedApplication, SecureToolRegistry, PermissionLevel, ToolCategory

def test_open_app_tool():
    tool = OpenApplicationTool()
    print("--- Tool Parameters Schema ---")
    print(tool.parameters)

    print("\n--- Testing Valid Whitelisted App Execution (notepad) ---")
    res1 = tool.execute("notepad")
    print("Result:", res1)

    print("\n--- Testing Case-Insensitive App Execution (CALCULATOR) ---")
    res2 = tool.execute("CALCULATOR")
    print("Result:", res2)

    print("\n--- Testing Non-Whitelisted App Rejection (malicious_script) ---")
    res3 = tool.execute("malicious_script")
    print("Result:", res3)

    print("\n--- Testing SecureToolRegistry Integration ---")
    registry = SecureToolRegistry()
    registry.register_tool(
        tool,
        category=ToolCategory.SYSTEM_EXECUTION,
        permission=PermissionLevel.SYSTEM_EXECUTION,
        requires_confirmation=False
    )

    reg_res = registry.execute_tool("open_application", {"app_name": "notepad"})
    print("Registry Execution Result:", reg_res)

if __name__ == "__main__":
    test_open_app_tool()
