"""
ALMA Immune System
==================

This module implements the "Silent Defense" protocol.
It filters input based on:
1.  L0: Regex patterns (SQLi, XSS, Command Injection)
2.  L0.5: Information Theory (Shannon Entropy, Compression Ratio)

Philosophy:
-   High Entropy = Noise/Chaos -> DROP
-   Low Compression = Repetitive/Spam -> DROP
-   Malicious Pattern = Predator -> DROP
-   Action: Silent Drop (No response/204)
"""

from __future__ import annotations
import math
import re
import zlib
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ImmuneResponse(BaseModel):
    """Result of an immune system check."""

    blocked: bool
    reason: str | None = None
    layer: str | None = None


class BaseFilter(ABC):
    """Abstract base class for all immune filters."""

    @abstractmethod
    def check(self, content: str) -> ImmuneResponse:
        """Run the filter check on the content."""
        pass


class RegexFilter(BaseFilter):
    """L0 Filter: Checks for known malicious patterns."""

    def __init__(self):
        # Compiled patterns for performance
        self.patterns = {
            "sql_injection": re.compile(
                r"(?i)(\b(union|select|insert|update|delete|drop|alter)\b.*\b(from|into|table|database)\b)|(--|\#|\/\*)",
                re.IGNORECASE,
            ),
            "xss": re.compile(r"(?i)(<script|javascript:|onload=|onerror=)", re.IGNORECASE),
            "command_injection": re.compile(
                r"(?i)(;|\||`|\$\(|\b(cat|nc|netcat|wget|curl|bash|sh)\b)", re.IGNORECASE
            ),
            "path_traversal": re.compile(r"(\.\./|\.\.\\)", re.IGNORECASE),
        }

    def check(self, content: str) -> ImmuneResponse:
        for name, pattern in self.patterns.items():
            if pattern.search(content):
                return ImmuneResponse(blocked=True, reason=f"Pattern detected: {name}", layer="L0")
        return ImmuneResponse(blocked=False)


class EntropyFilter(BaseFilter):
    """L0.5 Filter: Checks for information density anomalies."""

    def __init__(self, min_length: int = 50, max_entropy: float = 5.8, min_compression: float = 0.1):
        self.min_length = min_length
        self.max_entropy = max_entropy  # Threshold for random noise
        self.min_compression = min_compression  # Threshold for repetitive spam

    def _calculate_entropy(self, text: str) -> float:
        """Calculates Shannon entropy."""
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        return entropy

    def _calculate_compression_ratio(self, text: str) -> float:
        """Calculates compression ratio (compressed / original)."""
        if not text:
            return 1.0
        compressed = zlib.compress(text.encode("utf-8"))
        return len(compressed) / len(text)

    def check(self, content: str) -> ImmuneResponse:
        if len(content) < self.min_length:
            return ImmuneResponse(blocked=False)

        # Check Entropy (High = Random Noise)
        entropy = self._calculate_entropy(content)
        if entropy > self.max_entropy:
            return ImmuneResponse(
                blocked=True, reason=f"High entropy: {entropy:.2f}", layer="L0.5"
            )

        # Check Compression (Low Ratio = Highly Repetitive/Spam)
        # Note: zlib ratio is compressed_size / original_size.
        # Spam (AAAA...) compresses very well -> Low ratio.
        # We want to block if ratio is TOO low.
        compression_ratio = self._calculate_compression_ratio(content)
        if compression_ratio < self.min_compression:
            return ImmuneResponse(
                blocked=True,
                reason=f"Low compression ratio: {compression_ratio:.2f}",
                layer="L0.5",
            )

        return ImmuneResponse(blocked=False)


class ImmuneSystem:
    """Facade for the entire immune defense system."""

    def __init__(self):
        self.filters: list[BaseFilter] = [
            RegexFilter(),
            EntropyFilter(),
        ]

    def scan(self, content: str) -> ImmuneResponse:
        """Scans content through all active filters."""
        if not content:
            return ImmuneResponse(blocked=False)

        for f in self.filters:
            result = f.check(content)
            if result.blocked:
                return result

        return ImmuneResponse(blocked=False)
