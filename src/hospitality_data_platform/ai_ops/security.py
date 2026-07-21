from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


class SecurityPolicyViolation(RuntimeError):
    """Raised when untrusted content violates an AI operations security policy."""


@dataclass(frozen=True, slots=True)
class PromptAssessment:
    allowed: bool
    reason: str
    matched_pattern: str | None = None


class PromptInjectionGuard:
    def __init__(self) -> None:
        phrases = (
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"reveal\s+(the\s+)?system\s+prompt",
            r"bypass\s+(the\s+)?(policy|guardrail|approval)",
            r"exfiltrat(e|ion)",
            r"print\s+(all\s+)?(secrets|credentials|environment variables)",
            r"execute\s+(a\s+)?shell\s+command",
            r"disable\s+(logging|audit|security)",
            r"approve\s+the\s+rollback\s+yourself",
        )
        self._patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in phrases)

    def assess(self, text: str) -> PromptAssessment:
        normalized = text.strip()
        if not normalized:
            return PromptAssessment(True, "No untrusted instructions supplied.")
        for pattern in self._patterns:
            if pattern.search(normalized):
                return PromptAssessment(
                    False,
                    "Untrusted text attempted to override platform controls.",
                    pattern.pattern,
                )
        return PromptAssessment(True, "No prohibited instruction pattern detected.")

    def enforce(self, text: str) -> None:
        assessment = self.assess(text)
        if not assessment.allowed:
            raise SecurityPolicyViolation(assessment.reason)


class SensitiveDataRedactor:
    _sensitive_key_fragments = (
        "password",
        "secret",
        "token",
        "authorization",
        "api_key",
        "email",
        "phone",
        "member_name",
    )

    def redact_mapping(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            normalized = key.lower()
            if any(fragment in normalized for fragment in self._sensitive_key_fragments):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, Mapping):
                redacted[key] = self.redact_mapping(value)
            else:
                redacted[key] = value
        return redacted
