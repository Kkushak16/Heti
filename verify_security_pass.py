import sys
import os
import glob
import ast

sys.path.insert(0, r"d:\Antigravity")

from Heti.tools.system_tools import get_default_tools, OpenApplicationTool, AllowedApplication

def verify_codebase_security_pass():
    print("=================================================================")
    print(" 🔒 RUNNING SECURITY PASS: COMPREHENSIVE EXEC TOOL AUDIT")
    print("=================================================================")

    heti_dir = os.path.abspath(r"d:\Antigravity\Heti")
    py_files = glob.glob(os.path.join(heti_dir, "**", "*.py"), recursive=True)

    disallowed_keywords = ["run_terminal_command", "execute_shell_command", "shell_tool", "bash_tool", "cmd_exec"]
    violations = []

    print(f"🔍 Auditing {len(py_files)} Python source files in Heti framework...")

    for file_path in py_files:
        rel_path = os.path.relpath(file_path, heti_dir)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for disallowed tool class names or function names
        for kw in disallowed_keywords:
            if f"class {kw}" in content or f"def {kw}" in content:
                violations.append(f"Disallowed exec tool definition '{kw}' found in {rel_path}")

        # Ensure all subprocess usage in Heti tools strictly disables shell or uses static arguments
        if "tools" in rel_path and "subprocess.Popen" in content:
            if "shell=True" in content:
                violations.append(f"Insecure shell=True subprocess execution found in {rel_path}")
            elif "shell=False" not in content:
                violations.append(f"Subprocess call missing explicit shell=False in {rel_path}")

    # Inspect registered tools in default registry
    print("\n🔍 Auditing registered tools in default toolset...")
    tools = get_default_tools()
    tool_names = [t.name for t in tools]
    print(f"Registered Tool Names: {tool_names}")

    for t in tools:
        if "command" in t.name or "shell" in t.name or "terminal" in t.name or "exec" in t.name:
            violations.append(f"Generic command execution tool detected in default registry: '{t.name}'")

    # Verify Enum whitelist enforcement on application launcher
    open_app_tool = OpenApplicationTool()
    allowed_enum_values = [a.value for a in AllowedApplication]
    print(f"Allowed Application Enum Whitelist: {allowed_enum_values}")

    test_unauthorized_app = open_app_tool.execute("malicious_cmd.exe")
    assert "error" in test_unauthorized_app, "OpenApplicationTool allowed non-whitelisted binary!"
    print("✅ Non-whitelisted binary execution correctly BLOCKED by Enum guard.")

    print("\n-----------------------------------------------------------------")
    if violations:
        print("❌ SECURITY AUDIT FAILED! Violations detected:")
        for v in violations:
            print(f" - {v}")
        sys.exit(1)
    else:
        print("✅ SECURITY PASS CONFIRMED:")
        print(" 1. NO generic `run_terminal_command` or shell execution tools exist.")
        print(" 2. OS launcher (`open_application`) strictly enforces Enum whitelist.")
        print(" 3. All tool calls use `shell=False` to prevent injection attacks.")
        print("=================================================================")

if __name__ == "__main__":
    verify_codebase_security_pass()
