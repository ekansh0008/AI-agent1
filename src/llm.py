"""Thin wrapper around the Google Gemini API with retry + backoff.

Uses the `google-genai` SDK. A free API key is available from
https://aistudio.google.com/apikey
"""

from __future__ import annotations

import json
import re
import time


class LLMError(RuntimeError):
    pass


_SKIP_MODEL_PARTS = ("image", "tts", "embed", "aqa", "robotics", "computer", "live")


def _rank_models(names: list[str]) -> list[str]:
    """Prefer text-generation Gemini models, newest-looking first (flash > pro
    so we stay inside free-tier quotas)."""
    cleaned = []
    for n in names:
        nl = n.lower()
        if "gemini" not in nl or any(part in nl for part in _SKIP_MODEL_PARTS):
            continue
        cleaned.append(n)
    flashes = sorted((n for n in cleaned if "flash" in n.lower()), reverse=True)
    pros = sorted((n for n in cleaned if "pro" in n.lower() and n not in flashes), reverse=True)
    others = sorted(n for n in cleaned if n not in flashes and n not in pros)
    return flashes + pros + others


def _list_models(client) -> list[str]:
    """Models supporting generateContent for this key (best first)."""
    names: list[str] = []
    for m in client.models.list():
        name = (getattr(m, "name", "") or "").replace("models/", "")
        actions = getattr(m, "supported_actions", None) or []
        if actions and not any("generateContent" in str(a) for a in actions):
            continue
        if name:
            names.append(name)
    return _rank_models(names)


def available_models_for_key(api_key: str) -> list[str]:
    """Public helper: list usable model IDs for a key (for the UI)."""
    from google import genai

    client = genai.Client(api_key=api_key)
    return _list_models(client)


class LLMClient:
    def __init__(self, api_key: str, model: str = "gemini-3-flash"):
        if not api_key:
            raise LLMError(
                "No Gemini API key provided. Get a free key at "
                "https://aistudio.google.com/apikey and add it in the sidebar "
                "or in a .env file (GEMINI_API_KEY=...)."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise LLMError(
                "The 'google-genai' package is not installed. "
                "Run: pip install -r requirements.txt"
            ) from exc
        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._tried_model_discovery = False

    def generate(
        self,
        prompt: str,
        temperature: float = 0.55,
        max_output_tokens: int = 8192,
        max_retries: int = 5,
    ) -> str:
        """Generate text with exponential backoff on rate-limit / transient errors."""
        from google.genai import types

        config_kwargs = dict(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        # Gemini 3 models "think" by default; constrain thinking so the output
        # budget is spent on the actual text. Skipped gracefully on older SDKs.
        if self.model.startswith("gemini-3"):
            try:
                config_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.LOW
                )
            except (AttributeError, TypeError, ValueError):
                pass
        config = types.GenerateContentConfig(**config_kwargs)
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                text = (resp.text or "").strip()
                if not text:
                    raise LLMError("Model returned an empty response.")
                return text
            except Exception as exc:  # noqa: BLE001 - deliberate broad retry
                last_err = exc
                msg = str(exc)
                msg_low = msg.lower()
                # Model renamed/retired for this key? Discover what IS available
                # and switch automatically instead of failing.
                if (
                    ("NOT_FOUND" in msg or "not found" in msg_low or "404" in msg)
                    and not self._tried_model_discovery
                ):
                    self._tried_model_discovery = True
                    try:
                        discovered = _list_models(self.client)
                    except Exception:  # noqa: BLE001
                        discovered = []
                    if discovered:
                        self.model = discovered[0]
                        continue  # retry with the discovered model
                transient = any(
                    token in msg_low
                    for token in (
                        "429", "resource_exhausted", "rate", "quota",
                        "500", "502", "503", "unavailable", "deadline",
                        "overloaded", "timeout", "empty response",
                    )
                )
                if not transient or attempt == max_retries - 1:
                    raise
                wait = min(8 * (2 ** attempt), 90)
                time.sleep(wait)
        raise LLMError(f"Gemini request failed after retries: {last_err}")

    def generate_json(self, prompt: str, **kwargs) -> dict:
        """Generate a response and parse the first JSON object in it."""
        raw = self.generate(prompt, temperature=0.3, **kwargs)
        return extract_json(raw)


def extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from raw model output."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    if start == -1:
        raise LLMError(f"No JSON object found in model output: {cleaned[:200]}")
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start : i + 1])
                except json.JSONDecodeError as exc:
                    raise LLMError(
                        f"Malformed JSON in model output: {exc}"
                    ) from exc
    raise LLMError("Unbalanced braces in model JSON output.")
