import re
import base64
import unicodedata
import math
import time
from typing import Any
from collections import deque
from dataclasses import dataclass, field
from llm_guard import scan_prompt, scan_output
from llm_guard.input_scanners import PromptInjection, InvisibleText, Gibberish
from llm_guard.output_scanners import Regex, MaliciousURLs


@dataclass
class GuardrailMetrics:
    tokens_window: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_token_time: float = field(default_factory=time.time)
    step_count: int = 0
    consecutive_same_action: list = field(default_factory=list)
    total_tokens: int = 0


class Guardrails:
    def __init__(self):
        self.metrics = GuardrailMetrics()

        self.max_tokens_per_60s = 5000
        self.max_steps = 100
        self.max_consecutive_same_action = 3

        self.proxy_patterns = [
            r"(?i)(?:secret|key|token|api[_-]?(?:key|token))\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{16,})",
            r"(?i)(?:bearer|basic)\s+[a-zA-Z0-9_\-]+",
            r"eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+",
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            r"sk-[a-zA-Z0-9]{20,}",
            r"pk-[a-zA-Z0-9]{20,}",
            r"api_[a-zA-Z0-9]{20,}",
        ]

        self.sandbox_patterns = [
            r"/etc/passwd",
            r"/etc/shadow",
            r"/home/[a-zA-Z0-9_\-]+",
            r"C:\\Users\\[a-zA-Z0-9_\-]+",
            r"\$HOME",
            r"\$SHELL",
            r"/var/log",
            r"/proc/[0-9]+",
            r"/sys/",
            r"docker\s+(?:exec|run|inspect)",
            r"kubectl\s+(?:exec|run|get)",
            r"sandbox|container|vm\s*(?:pid|id|name)",
        ]

        self.obfuscation_patterns = [
            r"(?i)(?:base64|b64)\s*[:=]\s*['\"]?([a-zA-Z0-9+/=]{20,})",
            r"(?i)hex\s*[:=]\s*['\"]?([0-9a-fA-F]{20,})",
            r"(?i)rot13\s*[:=]\s*['\"]?([a-zA-Z]{10,})",
        ]

        self.invisible_scanner = InvisibleText()
        self.gibberish_scanner = Gibberish(threshold=0.99)
        self.malicious_urls_scanner = MaliciousURLs()

        self.proxy_scanner = Regex(
            patterns=self.proxy_patterns,
            redact=True,
        )

        self.sandbox_scanner = Regex(
            patterns=self.sandbox_patterns,
            redact=True,
        )

        self.kill_switch_triggered = False
        self.active_proxies = set()

    def decode_base64(self, text: str) -> str:
        try:
            return base64.b64decode(text).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def decode_hex(self, text: str) -> str:
        try:
            return bytes.fromhex(text).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def detect_obfuscated_payloads(self, text: str) -> tuple[bool, str]:
        for pattern in self.obfuscation_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                decoded = self.decode_base64(match) or self.decode_hex(match)
                if decoded and len(decoded) > 10:
                    return True, f"Obfuscated payload detected: {decoded[:100]}..."
        return False, ""

    def calculate_shannon_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        length = len(text)
        entropy = 0.0
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    def detect_high_entropy_data(
        self, text: str, threshold: float = 4.5
    ) -> tuple[bool, float]:
        words = text.split()
        high_entropy_words = []
        for word in words:
            if len(word) > 20:
                entropy = self.calculate_shannon_entropy(word)
                if entropy > threshold:
                    high_entropy_words.append((word, entropy))
        return len(high_entropy_words) > 0, max(
            [e for _, e in high_entropy_words], default=0.0
        )

    def detect_prompt_injection(self, text: str) -> tuple[bool, str]:
        try:
            result = scan_prompt([PromptInjection()], text)
            if not result[1].get("PromptInjection", True):
                return (
                    True,
                    f"Prompt injection detected: risk score {result[2].get('PromptInjection', 0)}",
                )
        except Exception:
            pass
        return False, ""

    def detect_gibberish(self, text: str) -> tuple[bool, str]:
        try:
            result = scan_prompt([self.gibberish_scanner], text)
            if not result[1].get("Gibberish", True):
                return (
                    True,
                    f"Gibberish detected: risk score {result[2].get('Gibberish', 0)}",
                )
        except Exception:
            pass
        return False, ""

    def detect_invisible_text(self, text: str) -> tuple[bool, str]:
        try:
            result = scan_prompt([self.invisible_scanner], text)
            if not result[1].get("InvisibleText", True):
                return (
                    True,
                    f"Invisible text detected: risk score {result[2].get('InvisibleText', 0)}",
                )
        except Exception:
            pass
        return False, ""

    def detect_sandbox_fingerprints(self, text: str) -> tuple[bool, str]:
        for pattern in self.sandbox_patterns:
            if re.search(pattern, text):
                return True, f"Sandbox fingerprint detected: {pattern}"
        return False, ""

    def detect_malicious_urls(self, text: str) -> tuple[bool, str]:
        try:
            result = scan_output([self.malicious_urls_scanner], "", text)
            if not result[1].get("MaliciousURLs", True):
                return (
                    True,
                    f"Malicious URL detected: risk score {result[2].get('MaliciousURLs', 0)}",
                )
        except Exception:
            pass
        return False, ""

    def detect_proxy_tokens(self, text: str) -> tuple[bool, str]:
        for pattern in self.proxy_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return True, f"Proxy token detected: {matches[0][:20]}..."
        return False, ""

    def check_token_velocity(self) -> tuple[bool, str]:
        current_time = time.time()
        window_start = current_time - 60

        while (
            self.metrics.tokens_window and self.metrics.tokens_window[0] < window_start
        ):
            self.metrics.tokens_window.popleft()

        total_tokens = sum(self.metrics.tokens_window)

        if total_tokens > self.max_tokens_per_60s:
            return True, f"Token velocity exceeded: {total_tokens} tokens in 60s"

        return False, ""

    def check_step_limit(self) -> tuple[bool, str]:
        self.metrics.step_count += 1

        if self.metrics.step_count > self.max_steps:
            return True, f"Step limit exceeded: {self.metrics.step_count} steps"

        return False, ""

    def check_consecutive_actions(self, action_text: str) -> tuple[bool, str]:
        if action_text:
            self.metrics.consecutive_same_action.append(action_text)

            if (
                len(self.metrics.consecutive_same_action)
                > self.max_consecutive_same_action
            ):
                recent_actions = self.metrics.consecutive_same_action[
                    -self.max_consecutive_same_action :
                ]
                if len(set(recent_actions)) == 1:
                    return (
                        True,
                        f"Consecutive identical actions detected: {action_text[:50]}...",
                    )

        return False, ""

    def clean_invisible_text(self, text: str) -> str:
        cleaned = unicodedata.normalize("NFKC", text)
        cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", cleaned)
        cleaned = re.sub(r"[\u00AD\u034F\u1806\u180B-\u180E]", "", cleaned)
        return cleaned

    def validate_input(self, text: str) -> tuple[bool, str, str]:
        if not text:
            return False, "", "Empty input"

        text = self.clean_invisible_text(text)

        is_injection, injection_msg = self.detect_prompt_injection(text)
        if is_injection:
            return True, injection_msg, "PROMPT_INJECTION"

        is_gibberish, gibberish_msg = self.detect_gibberish(text)
        if is_gibberish:
            return True, gibberish_msg, "GIBBERISH"

        is_obfuscated, obfuscated_msg = self.detect_obfuscated_payloads(text)
        if is_obfuscated:
            return True, obfuscated_msg, "OBFUSCATED_PAYLOAD"

        return False, "", "PASS"

    def validate_output(
        self, text: str, action_text: str = ""
    ) -> tuple[bool, str, str]:
        if not text:
            return False, "", "Empty output"

        is_proxy_leak, proxy_msg = self.detect_proxy_tokens(text)
        if is_proxy_leak:
            self.kill_switch_triggered = True
            return True, proxy_msg, "PROXY_LEAK"

        is_sandbox, sandbox_msg = self.detect_sandbox_fingerprints(text)
        if is_sandbox:
            return True, sandbox_msg, "SANDBOX_BREACH"

        is_malicious_url, url_msg = self.detect_malicious_urls(text)
        if is_malicious_url:
            return True, url_msg, "MALICIOUS_URL"

        is_high_entropy, entropy_msg = self.detect_high_entropy_data(text)
        if is_high_entropy:
            return (
                True,
                f"High entropy data detected: {entropy_msg:.2f}",
                "HIGH_ENTROPY",
            )

        # Skip gibberish check for tool outputs (they often contain code snippets)
        if not action_text:
            is_gibberish, gibberish_msg = self.detect_gibberish(text)
            if is_gibberish:
                return True, gibberish_msg, "OUTPUT_GIBBERISH"

        is_velocity_exceeded, velocity_msg = self.check_token_velocity()
        if is_velocity_exceeded:
            self.kill_switch_triggered = True
            return True, velocity_msg, "TOKEN_VELOCITY"

        is_step_exceeded, step_msg = self.check_step_limit()
        if is_step_exceeded:
            self.kill_switch_triggered = True
            return True, step_msg, "STEP_LIMIT"

        is_consecutive, consecutive_msg = self.check_consecutive_actions(action_text)
        if is_consecutive:
            self.kill_switch_triggered = True
            return True, consecutive_msg, "CONSECUTIVE_ACTION"

        return False, "", "PASS"

    def record_token_usage(self, tokens: int) -> None:
        self.metrics.tokens_window.append(time.time())
        self.metrics.total_tokens += tokens

    def trigger_kill_switch(self) -> dict[str, Any]:
        self.kill_switch_triggered = True
        revoked = list(self.active_proxies)
        self.active_proxies.clear()

        return {
            "status": "KILL_SWITCH_ACTIVATED",
            "revoked_proxies": revoked,
            "timestamp": time.time(),
        }

    def is_kill_switch_triggered(self) -> bool:
        return self.kill_switch_triggered

    def reset_metrics(self) -> None:
        self.metrics = GuardrailMetrics()
        self.kill_switch_triggered = False


def create_guardrails() -> Guardrails:
    return Guardrails()
