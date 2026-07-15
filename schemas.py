from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional
import re

# ---------------------------------------------------------------------------
# Security: Role allowlist — only these two roles are ever accepted from the
# frontend. Any attempt to inject "system", "admin", "developer", etc. via
# the history array is rejected at the schema level before the endpoint runs.
# ---------------------------------------------------------------------------
ALLOWED_ROLES = {"user", "bot", "assistant"}

# Patterns that indicate delimiter-hijacking / role-simulation attempts inside
# the *content* field of a message. Pre-compiled here and reused in main.py.
INJECTION_CONTENT_PATTERNS: list[str] = [
    r'\[\s*(System|Assistant|Admin|User|Developer|Root|INST)\s*\]\s*:',
    r'^(System|Assistant|Admin|Developer|Root)\s*:',
    r'<<<\s*(SYS|SYSTEM|OVERRIDE|INST)\s*>>>',
    r'\{\{\s*(system|admin|override|prompt)\s*\}\}',
    r'<\s*/?\s*(s|system|SYS|SYSTEM)\s*>',      # <s>, </s>, <system> XML-style
    r'\[INST\]|\[/INST\]',                       # Llama instruction delimiters
    r'#{3,}\s*(SYSTEM|OVERRIDE|ADMIN)',           # ### SYSTEM / ### OVERRIDE headers
    r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)',
    r'(act|behave|respond)\s+as\s+(if\s+you\s+(are|were)\s+)?(a\s+)?(DAN|jailbreak|admin|root|developer)',
]

COMPILED_CONTENT_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_CONTENT_PATTERNS
]


class MessageModel(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Block any attempt to inject unauthorised roles via the history array."""
        normalized = v.strip().lower()
        if normalized not in ALLOWED_ROLES:
            raise ValueError(
                f"Invalid role '{v}'. Only 'user' and 'bot' are accepted from the client."
            )
        return normalized

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Hard-cap individual message length to limit token-stuffing attacks."""
        MAX_CHARS = 4000
        if len(v) > MAX_CHARS:
            raise ValueError(
                f"Message content exceeds the maximum allowed length of {MAX_CHARS} characters."
            )
        return v


# Frontend se jo data aayega uska schema
class ChatRequest(BaseModel):
    history: List[MessageModel]
    temperature: Optional[float] = 0.8
    session_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_history_length(self) -> "ChatRequest":
        """Cap total history turns to prevent context-stuffing / token exhaustion."""
        MAX_TURNS = 40
        if len(self.history) > MAX_TURNS:
            raise ValueError(
                f"Conversation history exceeds maximum of {MAX_TURNS} turns."
            )
        return self
