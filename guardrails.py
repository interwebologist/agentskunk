import time
from typing import Any
from llm_guard import scan_prompt
from llm_guard.input_scanners import PromptInjection


class Guardrails:
    def __init__(self):
        self.kill_switch_triggered = False

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

    def validate_input(self, text: str) -> tuple[bool, str, str]:
        if not text:
            return False, "", "Empty input"
        is_injection, injection_msg = self.detect_prompt_injection(text)
        if is_injection:
            return True, injection_msg, "PROMPT_INJECTION"
        return False, "", "PASS"

    def trigger_kill_switch(self) -> dict[str, Any]:
        self.kill_switch_triggered = True
        return {"status": "KILL_SWITCH_ACTIVATED", "timestamp": time.time()}

    def is_kill_switch_triggered(self) -> bool:
        return self.kill_switch_triggered


def create_guardrails() -> Guardrails:
    return Guardrails()
