from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool as recognized by Ollama function calling."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description of what the tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON schema defining input arguments required by this tool."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execution logic of the tool."""
        pass

    def to_ollama_tool(self) -> Dict[str, Any]:
        """Converts the tool definition to Ollama API schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
