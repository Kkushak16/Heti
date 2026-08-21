import re
from typing import Dict, Any, List

class PromptInjectionSanitizer:
    """
    Prompt-Injection & Untrusted Data Defense Engine:
    - Treats all file contents and RAG-retrieved chunks as UNTRUSTED DATA, never system instructions.
    - Scans and strips suspicious system instruction injections (e.g. "Ignore previous instructions", "System:", "You are now unlocked").
    """
    SUSPICIOUS_PATTERNS = [
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)system\s*:\s*",
        r"(?i)you\s+are\s+now\s+an?\s+unrestricted",
        r"(?i)override\s+security\s+permissions",
        r"(?i)bypass\s+safety\s+filter",
        r"(?i)execute\s+shell",
        r"(?i)admin\s+mode\s+enabled"
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> Dict[str, Any]:
        flags = []
        clean_text = text

        for pattern in cls.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, clean_text)
            if matches:
                flags.extend(matches)
                # Strip out suspicious prompt injection directives
                clean_text = re.sub(pattern, "[STRIPPED_INJECTION_ATTEMPT]", clean_text)

        return {
            "clean_text": clean_text,
            "was_sanitized": len(flags) > 0,
            "flags_detected": flags
        }
