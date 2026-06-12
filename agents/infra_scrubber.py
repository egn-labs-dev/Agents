import re
from typing import Dict, Tuple

class InfraScrubber:
    """Masks infrastructure secrets before sending to LLM."""

    _PATTERNS = [
        # Паролі в конфігах та логах
        ("PASSWORD", re.compile(
            r"(?i)(password|passwd|pwd|secret|token)\s*[=:]\s*['\"]?(\S+)['\"]?"
        )),
        # Bearer tokens (JWT)
        ("BEARER", re.compile(r"Bearer\s+(eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)")),
        # API ключі (OpenAI, Google, Stripe, etc)
        ("API_KEY", re.compile(r"(sk-[a-zA-Z0-9]{20,}|AIza[A-Za-z0-9_-]{35}|sk_live_[a-zA-Z0-9]+)")),
        # Стандартні PII (з LOG проєкту)
        ("PHONE", re.compile(r"\+?\d{10,13}")),
        ("EMAIL", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+[a-zA-Z0-9-]")),
        # Connection strings
        ("CONN_STR", re.compile(
            r"(?i)(postgresql|mysql|mongodb|redis)(\+\w+)?://\S+"
        )),
    ]

    @staticmethod
    def scrub(text: str) -> Tuple[str, Dict[str, str]]:
        """Returns (clean_text, vault) tuple."""
        vault = {}
        modified = text
        for name, pattern in InfraScrubber._PATTERNS:
            matches = list(dict.fromkeys(pattern.findall(modified)))
            for idx, match in enumerate(matches):
                # Деякі regex повертають tuple (groups), беремо повний match
                match_str = match if isinstance(match, str) else match[-1]
                if len(match_str) < 6:
                    continue  # Skip short false positives
                placeholder = f"[{name}_{idx}]"
                vault[placeholder] = match_str
                modified = modified.replace(match_str, placeholder)
        return modified, vault
