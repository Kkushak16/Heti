from typing import List, Dict, Any

class ShortTermMemory:
    """Manages short-term conversation context and message history for Ollama chat."""

    def __init__(self, system_prompt: str = "You are Heti, a local agentic voice and task assistant."):
        self.system_prompt = system_prompt
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str = None, tool_calls: List[Dict[str, Any]] = None):
        msg = {"role": "assistant"}
        if content:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.history.append(msg)

    def add_tool_response(self, tool_name: str, content: Any):
        self.history.append({
            "role": "tool",
            "name": tool_name,
            "content": str(content)
        })

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.history

    def clear(self):
        self.history = [{"role": "system", "content": self.system_prompt}]
