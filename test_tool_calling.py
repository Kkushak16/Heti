import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_stats",
            "description": "Retrieves the current CPU, RAM, and disk utilization of the host machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "detailed": {
                        "type": "boolean",
                        "description": "Whether to include detailed process breakdown"
                    }
                },
                "required": []
            }
        }
    }
]

MODELS_TO_TEST = [
    {"name": "qwen2.5:7b", "tier": "Full Tier"},
    {"name": "llama3.1:8b", "tier": "Full Tier"},
    {"name": "qwen2.5:3b", "tier": "Lite Tier"},
    {"name": "qwen2.5:1.5b", "tier": "Lite Tier"}
]

def test_tool_calling(model_name: str, tier: str):
    print(f"\n==========================================")
    print(f" Testing Model: {model_name} [{tier}]")
    print(f"==========================================")

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "Can you check the current CPU and memory usage on my system in detail?"
            }
        ],
        "tools": TOOLS,
        "stream": False
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            message = res_data.get("message", {})
            tool_calls = message.get("tool_calls", [])

            print(f"Response Content: {message.get('content') or '(Empty - tool call triggered)'}")
            
            if tool_calls:
                print(f"\n SUCCESS! Tool call detected for {model_name}:")
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    print(f"  - Tool Name: {fn.get('name')}")
                    print(f"  - Arguments: {json.dumps(fn.get('arguments'), indent=2)}")
                return True
            else:
                print(f" NO TOOL CALL triggered. Model replied with plain text.")
                return False

    except urllib.error.URLError as e:
        print(f" Connection Error: {e}. Is Ollama running on http://127.0.0.1:11434?")
        return False
    except Exception as e:
        print(f" Error during test: {e}")
        return False

if __name__ == "__main__":
    print("--- Heti Agent: Ollama Tool-Calling Verification ---")
    results = {}
    for item in MODELS_TO_TEST:
        model = item["name"]
        tier = item["tier"]
        success = test_tool_calling(model, tier)
        results[model] = success

    print("\n==========================================")
    print(" SUMMARY RESULTS")
    print("==========================================")
    for model, status in results.items():
        symbol = "✓ PASS" if status else "✗ FAIL / SKIPPED"
        print(f" - {model:15s}: {symbol}")
