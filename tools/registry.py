import os
import sys
from enum import Enum
from typing import Dict, Any, List, Optional, Callable

from .base import BaseTool

class PermissionLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    FILE_SYSTEM = "FILE_SYSTEM"
    SYSTEM_INFO = "SYSTEM_INFO"
    SYSTEM_EXECUTION = "SYSTEM_EXECUTION"
    DESTRUCTIVE = "DESTRUCTIVE"

class ToolCategory(str, Enum):
    SYSTEM_INFO = "SYSTEM_INFO"
    FILE_SYSTEM = "FILE_SYSTEM"
    NETWORK = "NETWORK"
    SYSTEM_EXECUTION = "SYSTEM_EXECUTION"
    CUSTOM = "CUSTOM"

try:
    from pydantic import BaseModel, create_model, ValidationError
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

class SecurityException(Exception):
    """Raised when a tool call fails security permission checks."""
    pass

class SecureToolRegistry:
    """
    Security Backbone for Heti Agent:
    - Enum Category & Permission Level Whitelisting
    - Pydantic Input Schema Validation
    - Permissions Policy Flag Checks (permissions.yaml)
    - Human-In-The-Loop (HITL) Confirmation Engine
    """

    def __init__(self, permissions_config: Optional[Dict[str, Any]] = None, hitl_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None, audit_log_path: str = "audit_log.jsonl"):
        self.permissions_config = permissions_config or {}
        self.hitl_callback = hitl_callback or self._default_hitl_prompt
        self.audit_log_path = audit_log_path
        self._registered_tools: Dict[str, BaseTool] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}

    def log_audit(self, tool_name: str, args: Dict[str, Any], status: str, result: Any, error: Optional[str] = None):
        import datetime
        import json

        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tool_name": tool_name,
            "category": self._tool_metadata.get(tool_name, {}).get("category", "UNKNOWN"),
            "permission": self._tool_metadata.get(tool_name, {}).get("permission", "UNKNOWN"),
            "args": args,
            "status": status,
            "result": str(result) if result is not None else None,
            "error": error
        }

        try:
            # Lite Tier Disk Guard: Log Rotation & Size Capping (Max 1MB per log file)
            if os.path.exists(self.audit_log_path) and os.path.getsize(self.audit_log_path) > 1 * 1024 * 1024:
                rotated_path = f"{self.audit_log_path}.1"
                if os.path.exists(rotated_path):
                    os.remove(rotated_path)
                os.rename(self.audit_log_path, rotated_path)

            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"⚠️ Audit logging failed: {e}")



    def register_tool(
        self,
        tool: BaseTool,
        category: ToolCategory = ToolCategory.CUSTOM,
        permission: PermissionLevel = PermissionLevel.READ_ONLY,
        requires_confirmation: bool = False
    ):
        name = tool.name
        policy = self.permissions_config.get("tools", {}).get(name, {})
        allowed = policy.get("allowed", True)
        requires_conf = policy.get("requires_confirmation", requires_confirmation)
        perm_level = policy.get("permission", permission.value)
        cat_level = policy.get("category", category.value)

        self._registered_tools[name] = tool
        self._tool_metadata[name] = {
            "category": cat_level,
            "permission": perm_level,
            "allowed": allowed,
            "requires_confirmation": requires_conf
        }
        print(f"🔒 [SecureRegistry] Registered '{name}' | Permission: {perm_level} | Allowed: {allowed} | HITL: {requires_conf}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._registered_tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        allowed_tools = []
        for name, tool in self._registered_tools.items():
            if self._tool_metadata[name]["allowed"]:
                allowed_tools.append(tool)
        return allowed_tools

    def validate_args(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        if not tool:
            raise SecurityException(f"Tool '{tool_name}' is not registered in SecureToolRegistry.")

        schema = tool.parameters

        if HAS_PYDANTIC and schema.get("properties"):
            fields = {}
            for param_name, details in schema.get("properties", {}).items():
                param_type = str
                if details.get("type") == "boolean":
                    param_type = bool
                elif details.get("type") == "integer":
                    param_type = int
                elif details.get("type") == "number":
                    param_type = float

                is_required = param_name in schema.get("required", [])
                default_val = ... if is_required else None
                fields[param_name] = (param_type, default_val)

            DynamicModel = create_model(f"{tool_name}_ArgsModel", **fields)
            try:
                validated_obj = DynamicModel(**args)
                return validated_obj.model_dump() if hasattr(validated_obj, "model_dump") else validated_obj.dict()
            except ValidationError as ve:
                raise SecurityException(f"Pydantic Schema Validation Failed for tool '{tool_name}': {ve}")
        
        return args

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        tool = self.get_tool(tool_name)
        if not tool:
            err = f"Security Alert: Attempted execution of unregistered tool '{tool_name}'."
            self.log_audit(tool_name, args, "DENIED", None, error=err)
            raise SecurityException(err)

        meta = self._tool_metadata[tool_name]

        if not meta["allowed"]:
            err = f"Security Denied: Tool '{tool_name}' is disabled in permissions policy (allowed=false)."
            self.log_audit(tool_name, args, "DENIED", None, error=err)
            raise SecurityException(err)

        try:
            validated_args = self.validate_args(tool_name, args)
        except SecurityException as val_err:
            self.log_audit(tool_name, args, "VALIDATION_FAILED", None, error=str(val_err))
            raise val_err

        if meta["requires_confirmation"]:
            print(f"⚠️ [HITL Alert] Security policy requires user confirmation for '{tool_name}' [{meta['permission']}].")
            confirmed = self.hitl_callback(tool_name, validated_args)
            if not confirmed:
                err = f"Execution Cancelled: User rejected HITL confirmation for tool '{tool_name}'."
                self.log_audit(tool_name, validated_args, "CANCELLED_HITL", None, error=err)
                raise SecurityException(err)

        try:
            res = tool.execute(**validated_args)
            self.log_audit(tool_name, validated_args, "SUCCESS", res)
            return res
        except Exception as exec_err:
            self.log_audit(tool_name, validated_args, "EXECUTION_ERROR", None, error=str(exec_err))
            raise exec_err

    def _default_hitl_prompt(self, tool_name: str, args: Dict[str, Any]) -> bool:
        print(f"\n✋ HUMAN-IN-THE-LOOP (HITL) CONFIRMATION REQUIRED")
        print(f" Tool: {tool_name}")
        print(f" Arguments: {args}")
        user_input = input(" Do you authorize execution? (y/N): ").strip().lower()
        return user_input in ["y", "yes"]
