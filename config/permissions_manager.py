import os
import sys
import yaml
from typing import Dict, Any

class PermissionsManager:
    """
    Permissions Settings Panel & Policy Enforcement Manager for Heti Agent.
    Allows CLI/GUI management of permissions.yaml and enforces toggling permissions
    (e.g., can_control_pc = False) to block tools like open_application.
    """
    def __init__(self, permissions_path: str = None):
        if permissions_path is None:
            permissions_path = os.path.join(os.path.dirname(__file__), "permissions.yaml")
        self.permissions_path = permissions_path
        self.config = self.load_permissions()

    def load_permissions(self) -> Dict[str, Any]:
        if not os.path.exists(self.permissions_path):
            return {"strict_mode": True, "allow_unlisted_tools": False, "can_control_pc": True, "tools": {}}

        with open(self.permissions_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if "can_control_pc" not in data:
            data["can_control_pc"] = True
        return data

    def save_permissions(self):
        with open(self.permissions_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False)
        print(" 💾 Permissions policy updated and saved to permissions.yaml")

    def toggle_control_pc(self, enabled: bool):
        """Toggles the global PC control switch (can_control_pc)."""
        self.config["can_control_pc"] = enabled
        if "open_application" in self.config.get("tools", {}):
            self.config["tools"]["open_application"]["allowed"] = enabled
        self.save_permissions()
        print(f" 🛡️ Global PC Control (can_control_pc) set to: {enabled}")

    def is_tool_allowed(self, tool_name: str) -> bool:
        if not self.config.get("can_control_pc", True) and tool_name == "open_application":
            return False

        tool_cfg = self.config.get("tools", {}).get(tool_name, {})
        return tool_cfg.get("allowed", True)

    def print_menu(self):
        print("=================================================================")
        print(" ⚙️ HETI PERMISSIONS & SECURITY POLICY PANEL")
        print("=================================================================")
        print(f" 1. Strict Mode                 : {self.config.get('strict_mode', True)}")
        print(f" 2. Allow Unlisted Tools        : {self.config.get('allow_unlisted_tools', False)}")
        print(f" 3. Can Control PC (App Launch) : {self.config.get('can_control_pc', True)}")
        print(" -----------------------------------------------------------------")
        print(" Configured Tools Policy:")
        for tool_name, info in self.config.get("tools", {}).items():
            allowed_str = "ALLOWED" if info.get("allowed") else "BLOCKED"
            confirm_str = " (HITL Confirm Req)" if info.get("requires_confirmation") else ""
            print(f"  • {tool_name:<25} [{info.get('permission'):<12}] -> {allowed_str}{confirm_str}")
        print("=================================================================\n")

if __name__ == "__main__":
    pm = PermissionsManager()
    pm.print_menu()
