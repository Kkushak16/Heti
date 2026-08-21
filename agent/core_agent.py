import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, TypedDict

from Heti.config.config_loader import Config
from Heti.config.safe_io import setup_safe_io, safe_print
from Heti.tools.base import BaseTool
from Heti.tools.registry import SecureToolRegistry, SecurityException, ToolCategory, PermissionLevel
from Heti.memory.short_term import ShortTermMemory

setup_safe_io()


def is_ollama_running(host: str) -> bool:
    """Quick health-check ping to Ollama before any LLM call."""
    try:
        urllib.request.urlopen(f"{host}/api/tags", timeout=3)
        return True
    except Exception:
        return False


# Check if langgraph is available for Full Tier graph workflow
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    next_step: str
    last_response: str


class HetiAgent:
    def __init__(self, config: Config = None, registry: Optional[SecureToolRegistry] = None):
        self.config = config or Config()
        self.memory = ShortTermMemory()
        self.registry = registry or SecureToolRegistry(permissions_config=self.config.permissions_config)
        self.max_iterations = 5  # Guard against infinite tool invocation loops

        # Auto-register default system tools if creating a fresh registry
        if registry is None:
            from Heti.tools.system_tools import get_default_tools
            for tool in get_default_tools():
                self.register_tool(tool)

    def register_tool(
        self,
        tool: BaseTool,
        category: ToolCategory = ToolCategory.CUSTOM,
        permission: PermissionLevel = PermissionLevel.READ_ONLY,
        requires_confirmation: bool = False
    ):
        self.registry.register_tool(
            tool,
            category=category,
            permission=permission,
            requires_confirmation=requires_confirmation
        )

    def run_turn(self, user_input: str) -> str:
        """
        Executes a complete interaction turn:
        user input -> intent check / tool execution -> response.
        """
        # Extract raw user prompt if wrapped by RAG context
        raw_query = user_input
        if "[USER QUERY]" in user_input:
            raw_query = user_input.split("[USER QUERY]", 1)[-1].strip()
        elif "User Query:" in user_input:
            raw_query = user_input.split("User Query:", 1)[-1].strip()
        elif "Query:" in user_input:
            raw_query = user_input.split("Query:", 1)[-1].strip()

        user_lower = raw_query.strip().lower()
        import re
        clean_text = re.sub(r'[^\w\s]', ' ', user_lower)
        words = set(clean_text.split())

        # ── Fuzzy Intent Matching (natural language support) ─────────────
        OPEN = {"open", "launch", "start", "run", "show", "view", "enable", "turn"}
        CLOSE = {"close", "stop", "kill", "exit", "quit", "end", "shut", "disable"}

        def _has(word_set):
            return bool(words & word_set)

        # 1. Camera ("open camera", "open the camera application", "launch webcam", "close camera")
        CAM_WORDS = {"camera", "cam", "webcam"}
        if _has(CAM_WORDS):
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "camera"})
                return "Closed camera app." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "camera"})
                return "Opened camera app." if "error" not in res else res["error"]

        # 0. Handless Mode Gesture Control ("enable handless mode", "turn on camera control", "stop handless mode", "gesture status")
        HANDLESS_TERMS = ["handless", "gesture control", "camera control", "hand gesture"]
        if any(term in clean_text for term in HANDLESS_TERMS):
            if any(w in words for w in ["status", "state", "check", "info", "fps"]):
                res = self.registry.execute_tool("get_gesture_status", {})
                if "error" in res:
                    return res["error"]
                st = "Active" if res.get("enabled") else "Inactive"
                fps = res.get("fps", 0)
                return f"Handless Mode is currently {st} operating at {fps} FPS."
            elif any(w in words for w in ["off", "stop", "disable", "deactivate", "close", "turn off"]):
                res = self.registry.execute_tool("toggle_handless_mode", {"enable": False})
                return "Handless Mode disabled. Camera turned off." if "error" not in res else res["error"]
            else:
                res = self.registry.execute_tool("toggle_handless_mode", {"enable": True})
                return "Handless Mode enabled. Camera active for gesture control." if "error" not in res else res["error"]

        # 2. File Explorer / File Manager ("open file manager", "open the file manager application", "open files", "open explorer", "close file manager")

        EXPLORER_TERMS = ["file manager", "file explorer", "my files", "my computer", "this pc", "file_manager"]
        if any(term in clean_text for term in EXPLORER_TERMS) or (_has({"explorer", "files", "folders"}) and _has(OPEN | CLOSE)):
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "explorer"})
                return "Closed File Explorer." if "error" not in res else res["error"]
            else:
                res = self.registry.execute_tool("open_application", {"app_name": "explorer"})
                return "Opened File Explorer." if "error" not in res else res["error"]

        # 3. Browser & Specific Applications ("open google chrome", "open chrome", "open edge", "open firefox", "open brave", "open browser")
        if "chrome" in words or "google chrome" in user_lower:
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "chrome"})
                return "Closed Google Chrome." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "chrome"})
                return "Opened Google Chrome." if "error" not in res else res["error"]

        if "edge" in words or "msedge" in words or "microsoft edge" in user_lower:
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "edge"})
                return "Closed Microsoft Edge." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "edge"})
                return "Opened Microsoft Edge." if "error" not in res else res["error"]

        if "firefox" in words or "mozilla firefox" in user_lower:
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "firefox"})
                return "Closed Firefox." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "firefox"})
                return "Opened Firefox." if "error" not in res else res["error"]

        if "brave" in words:
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "brave"})
                return "Closed Brave." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "brave"})
                return "Opened Brave." if "error" not in res else res["error"]

        BROWSER_WORDS = {"browser", "internet", "web"}
        if _has(BROWSER_WORDS):
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "browser"})
                return "Closed browser." if "error" not in res else res["error"]
            elif _has(OPEN) or "tab" not in words:
                res = self.registry.execute_tool("open_browser", {"url": "https://www.google.com"})
                return "Opened browser." if "error" not in res else res["error"]

        # 4. Direct URL / Website Navigation ("search youtube.com", "open youtube.com", "go to github.com", "open youtube")
        url_match = re.search(r'\b([a-zA-Z0-9-]+\.(com|org|net|io|edu|gov|in|co|ai|dev))\b', user_lower)
        if url_match:
            target_domain = url_match.group(1)
            full_target = f"https://{target_domain}"
            res = self.registry.execute_tool("open_browser", {"url": full_target})
            return f"Navigated to {target_domain}." if "error" not in res else res["error"]

        KNOWN_SITES = {"youtube": "https://youtube.com", "github": "https://github.com", "google": "https://google.com", "reddit": "https://reddit.com", "wikipedia": "https://wikipedia.org", "amazon": "https://amazon.com"}
        for site_key, site_url in KNOWN_SITES.items():
            if site_key in words and (_has(OPEN | {"search", "go", "visit", "navigate"}) or len(words) <= 3):
                res = self.registry.execute_tool("open_browser", {"url": site_url})
                return f"Navigated to {site_key}.com." if "error" not in res else res["error"]

        # 4. Notepad / Text Editor ("open notepad", "open text editor", "close notepad")
        NOTE_WORDS = {"notepad", "notes", "editor"}
        if _has(NOTE_WORDS) or "text editor" in clean_text:
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "notepad"})
                return "Closed Notepad." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "notepad"})
                return "Opened Notepad." if "error" not in res else res["error"]

        # 5. Calculator ("open calculator", "open calc", "close calculator")
        CALC_WORDS = {"calculator", "calc"}
        if _has(CALC_WORDS):
            if _has(CLOSE):
                res = self.registry.execute_tool("close_application", {"app_name": "calculator"})
                return "Closed Calculator." if "error" not in res else res["error"]
            elif _has(OPEN) or len(words) <= 4:
                res = self.registry.execute_tool("open_application", {"app_name": "calculator"})
                return "Opened Calculator." if "error" not in res else res["error"]

        # Generic "close X" fallback
        if _has(CLOSE) and len(words) <= 4:
            remaining = words - CLOSE - {"the", "app", "application", "please", "my"}
            if remaining:
                app_target = remaining.pop()
                res = self.registry.execute_tool("close_application", {"app_name": app_target})
                return res.get("message", res.get("error", f"Closed {app_target}."))

        if "new tab" in user_lower or ("tab" in words and bool(words & OPEN)):
            url_part = user_lower
            for strip_word in ["open", "new", "tab", "a", "the", "in", "to", "please"]:
                url_part = url_part.replace(strip_word, "")
            url_part = url_part.strip()
            if url_part and ("." in url_part or "http" in url_part):
                res = self.registry.execute_tool("open_new_tab", {"url": url_part})
            else:
                import webbrowser
                webbrowser.open("https://www.google.com", new=2)
                return "Opened new tab."
            return res.get("message", res.get("error", "Opened new tab."))

        # ── Web Search ───────────────────────────────────────────────────
        SEARCH = {"search", "google", "look", "find", "lookup"}
        if bool(words & SEARCH) and len(words) > 1:
            # Extract query: remove action words
            query_words = [w for w in user_lower.split() if w not in SEARCH and w not in {"for", "up", "the", "a", "on", "web", "please"}]
            query_text = " ".join(query_words).strip()
            if query_text:
                res = self.registry.execute_tool("web_search", {"query": query_text})
                return res.get("message", res.get("error", f"Searched for '{query_text}'."))

        # ── Screen Perception & Context ──────────────────────────────────
        SCREEN_WORDS = {"screen", "display", "window", "desktop"}
        if bool(words & SCREEN_WORDS):
            # Option 1: Visual In-Memory analysis requested
            if bool(words & {"visual", "photo", "picture", "image", "look", "see"}):
                res = self.registry.execute_tool("analyze_screen_in_memory", {"prompt": raw_query})
                return res.get("message", res.get("error", "Analyzed screen in memory."))
            # Option 2: Default fast & secure text-only UI context inspection
            elif bool(words & {"what", "check", "context", "open", "read", "inspect", "show", "current", "active"}) or "looking at" in user_lower:
                res = self.registry.execute_tool("get_screen_context", {})
                if "error" in res:
                    return res["error"]
                return res.get("message", "Inspected active screen context.")

        if bool(words & {"screenshot"}) and bool(words & {"take", "capture", "grab", "save"}):
            res = self.registry.execute_tool("take_screenshot", {"save_path": "screenshot.png"})
            return res.get("message", res.get("error", "Took screenshot."))

        # ── File operations ──────────────────────────────────────────────
        if "open file " in user_lower:
            file_target = raw_query.split("open file ", 1)[-1].strip().split("\n")[0]
            res = self.registry.execute_tool("open_file", {"file_path": file_target})
            return res.get("message", res.get("error", "Opened file."))

        if "create file " in user_lower:
            target_str = raw_query.split("create file ", 1)[-1].strip().split("\n")[0]
            parts = target_str.split(" with content ", 1)
            file_target = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            res = self.registry.execute_tool("create_file", {"file_path": file_target, "content": content})
            return res.get("message", res.get("error", "Created file."))

        if "delete file " in user_lower or "remove file " in user_lower:
            kw_used = "delete file " if "delete file " in user_lower else "remove file "
            file_target = raw_query.split(kw_used, 1)[-1].strip().split("\n")[0]
            res = self.registry.execute_tool("delete_file", {"file_path": file_target})
            return res.get("message", res.get("error", "Deleted file."))

        self.memory.add_user_message(user_input)

        if self.config.active_tier == "full" and HAS_LANGGRAPH:
            return self._run_turn_langgraph()
        else:
            return self._run_turn_lite_loop()

    def _call_ollama(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Fast health check — fail immediately instead of hanging 60s
        if not is_ollama_running(self.config.ollama_host):
            msg = (
                "Ollama is not running. Please start it first: open a terminal and run `ollama serve`."
            )
            safe_print(f" ❌ [Ollama Offline] {msg}")
            return {"content": msg}

        allowed_tools = self.registry.get_all_tools()
        tools_schema = [t.to_ollama_tool() for t in allowed_tools]

        payload = {
            "model": self.config.llm_name,
            "messages": messages,
            "options": {
                "num_ctx": self.config.num_ctx,
                "temperature": self.config.temperature
            },
            "stream": False
        }
        if tools_schema:
            payload["tools"] = tools_schema

        req = urllib.request.Request(
            f"{self.config.ollama_host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        safe_print(f" ⏳ [Heti] Thinking... (model: {self.config.llm_name})", end="", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                safe_print(" ✓")
                return res_data.get("message", {})
        except urllib.error.URLError as e:
            safe_print(" ✗")
            return {"content": f"Ollama Connection Error: {e}"}
        except Exception as e:
            safe_print(" ✗")
            return {"content": f"Execution Error: {e}"}


    def _check_ram_headroom(self, min_free_mb: float = 500.0) -> Optional[str]:
        """Checks free RAM headroom using psutil if available. Returns error warning string if memory is low."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            free_mb = mem.available / (1024 * 1024)
            if free_mb < min_free_mb:
                return f"RAM Headroom Warning: Low free memory ({round(free_mb, 1)}MB available < {min_free_mb}MB limit). Tool execution blocked to prevent OOM crash."
        except Exception:
            pass
        return None

    def _run_turn_lite_loop(self) -> str:
        """
        Lite Tier Agent Loop: Plain Python while-loop.
        Zero framework overhead (saves ~150MB RAM compared to full agent graph frameworks).
        Iterates user input -> LLM -> tool selection -> validated execution -> final response.
        Enforces a RAM headroom check to guard against low-memory (< 500MB free) execution crashes.
        """
        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1
            messages = self.memory.get_messages()
            message = self._call_ollama(messages)
            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                self.memory.add_assistant_message(
                    content=message.get("content"),
                    tool_calls=tool_calls
                )

                for tc in tool_calls:
                    fn = tc.get("function", {})
                    tool_name = fn.get("name")
                    args = fn.get("arguments", {})

                    # RAM Headroom Safety Check (< 500MB free RAM warning/block)
                    ram_warning = self._check_ram_headroom(min_free_mb=500.0)
                    if ram_warning:
                        print(f" ⚠️ [Lite Loop OOM Guard] {ram_warning}")
                        result = {"error": ram_warning}
                        self.memory.add_tool_response(tool_name, result)
                        continue

                    print(f" ⚙️ [Lite Loop] Requesting Secure Tool Execution: '{tool_name}' with args: {args}")
                    try:
                        result = self.registry.execute_tool(tool_name, args)
                    except SecurityException as sec_err:
                        print(f" ❌ [Security Block] {sec_err}")
                        result = {"error": str(sec_err)}

                    self.memory.add_tool_response(tool_name, result)
            else:
                content = message.get("content", "")
                self.memory.add_assistant_message(content=content)
                return content

        return "Max tool iteration limit reached."


    def _run_turn_langgraph(self) -> str:
        """
        Full Tier Agent Loop: LangGraph StateGraph flow.
        Provides explicit state transitions for complex agentic workflows.
        """
        def call_llm_node(state: AgentState) -> AgentState:
            msg = self._call_ollama(state["messages"])
            tool_calls = msg.get("tool_calls", [])
            content = msg.get("content", "")

            if tool_calls:
                self.memory.add_assistant_message(content=content, tool_calls=tool_calls)
                state["messages"] = self.memory.get_messages()
                state["next_step"] = "execute_tools"
            else:
                self.memory.add_assistant_message(content=content)
                state["messages"] = self.memory.get_messages()
                state["last_response"] = content
                state["next_step"] = "end"
            return state

        def execute_tools_node(state: AgentState) -> AgentState:
            last_msg = state["messages"][-1]
            tool_calls = last_msg.get("tool_calls", [])

            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name")
                args = fn.get("arguments", {})

                print(f" ⚙️ [LangGraph Loop] Requesting Secure Tool Execution: '{tool_name}' with args: {args}")
                try:
                    result = self.registry.execute_tool(tool_name, args)
                except SecurityException as sec_err:
                    print(f" ❌ [Security Block] {sec_err}")
                    result = {"error": str(sec_err)}

                self.memory.add_tool_response(tool_name, result)

            state["messages"] = self.memory.get_messages()
            state["next_step"] = "call_llm"
            return state

        def router(state: AgentState) -> str:
            return state["next_step"]

        workflow = StateGraph(AgentState)
        workflow.add_node("call_llm", call_llm_node)
        workflow.add_node("execute_tools", execute_tools_node)

        workflow.set_entry_point("call_llm")
        workflow.add_conditional_edges(
            "call_llm",
            router,
            {
                "execute_tools": "execute_tools",
                "end": END
            }
        )
        workflow.add_edge("execute_tools", "call_llm")

        graph = workflow.compile()
        initial_state: AgentState = {
            "messages": self.memory.get_messages(),
            "next_step": "call_llm",
            "last_response": ""
        }
        final_state = graph.invoke(initial_state)
        return final_state.get("last_response", "")

