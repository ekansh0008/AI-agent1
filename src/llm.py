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


class LLMClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
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

    def generate(
        self,
        prompt: str,
        temperature: float = 0.55,
        max_output_tokens: int = 8192,
        max_retries: int = 5,
    ) -> str:
        """Generate text with exponential backoff on rate-limit / transient errors."""
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
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
                msg = str(exc).lower()
                transient = any(
                    token in msg
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
