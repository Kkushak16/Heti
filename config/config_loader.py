import os
import sys

def load_yaml_simple(file_path: str) -> dict:
    try:
        import yaml
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        data = {}
        current_section = None
        current_subsection = None

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.split("#")[0].strip()
                if not line:
                    continue

                if line.endswith(":") and not ":" in line[:-1]:
                    key = line[:-1].strip()
                    if line.startswith("  "):
                        current_subsection = key
                        data[current_section][current_subsection] = {}
                    else:
                        current_section = key
                        current_subsection = None
                        data[current_section] = {}
                elif ":" in line:
                    parts = line.split(":", 1)
                    k = parts[0].strip()
                    v = parts[1].strip().strip('"').strip("'")
                    if v.isdigit():
                        v = int(v)
                    elif v.replace(".", "", 1).isdigit():
                        v = float(v)

                    if current_subsection and current_section:
                        data[current_section][current_subsection][k] = v
                    elif current_section:
                        data[current_section][k] = v
                    else:
                        data[k] = v
        return data

class Config:
    def __init__(self, config_path: str = None, permissions_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        if permissions_path is None:
            permissions_path = os.path.join(os.path.dirname(__file__), "permissions.yaml")

        self.raw_config = load_yaml_simple(config_path)
        self.permissions_config = load_yaml_simple(permissions_path) if os.path.exists(permissions_path) else {}

        self.active_tier = self.raw_config.get("tier", "full")
        self.system = self.raw_config.get("system", {})
        self.ollama_host = self.system.get("ollama_host", "http://127.0.0.1:11434")

        models_config = self.raw_config.get("models", {})
        if self.active_tier not in models_config:
            raise ValueError(f"Invalid tier '{self.active_tier}' configured in config.yaml. Must be 'full' or 'lite'.")

        self.model_settings = models_config[self.active_tier]
        self.llm_name = self.model_settings.get("llm_name")
        self.num_ctx = self.model_settings.get("num_ctx")
        self.temperature = self.model_settings.get("temperature", 0.2)
        self.stt_model = self.model_settings.get("stt_model", "tiny")
        self.stt_compute_type = self.model_settings.get("stt_compute_type", "int8")
        self.tts_voice = self.model_settings.get("tts_voice", "en_US-lessac-low")
        self.wake_word_engine = self.model_settings.get("wake_word_engine", "porcupine")
        self.wake_words = self.model_settings.get("wake_words", ["jarvis"])
        self.auto_unload_stt = self.model_settings.get("auto_unload_stt", True)
        self.embedding_model = self.model_settings.get("embedding_model", "all-MiniLM-L6-v2")
        self.rag_top_k = self.model_settings.get("rag_top_k", 2)
        self.rag_chunk_size = self.model_settings.get("rag_chunk_size", 256)
        self.rag_persist_mode = self.model_settings.get("rag_persist_mode", "disk_only")
        self.rag_summarize_retrieved = self.model_settings.get("rag_summarize_retrieved", True)

    def print_summary(self):
        print(f"==========================================")
        print(f" 🤖 HETI AGENT CONFIGURATION LOADED")
        print(f"==========================================")
        print(f" • Active Tier  : {self.active_tier.upper()}")
        print(f" • LLM Model    : {self.llm_name}")
        print(f" • Context Window: {self.num_ctx} tokens")
        print(f" • Temperature  : {self.temperature}")
        print(f" • STT Model    : {self.stt_model} ({self.stt_compute_type})")
        print(f" • RAG Embedding: {self.embedding_model} (k={self.rag_top_k}, chunk={self.rag_chunk_size})")
        print(f" • RAG Mode     : {self.rag_persist_mode}")
        print(f" • TTS Voice    : {self.tts_voice}")
        print(f" • Wake Engine  : {self.wake_word_engine}")
        print(f" • Ollama Host  : {self.ollama_host}")
        print(f"==========================================\n")



if __name__ == "__main__":
    cfg = Config()
    cfg.print_summary()
