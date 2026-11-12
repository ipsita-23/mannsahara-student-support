"""Replaceable local instruction-tuned LLM interface. No transcripts are written."""

import json
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parent.parent
OPTIONS = {"temperature": 0, "seed": 47309, "num_ctx": 2048, "num_predict": 140}
SCHEMA = {
    "type": "object",
    "properties": {"route": {"type": "string", "enum": ["ROUTINE", "CLARIFY", "ESCALATE"]}},
    "required": ["route"],
    "additionalProperties": False,
}


def prompt_version() -> str:
    """Read actual prompt revisions so logs cannot silently retain an older hardcoded version."""
    return "/".join(
        (ROOT / "prompts" / name).read_text().splitlines()[0].removeprefix("Revision: ").strip()
        for name in ["classifier.txt", "support.txt"]
    )


class BackendError(Exception):
    """Sanitized failure; upstream errors and request content must not reach the UI/log."""


class Backend(Protocol):
    def classify(self, messages: list[dict]) -> str: ...
    def generate(self, messages: list[dict]) -> str: ...
    def metadata(self) -> dict: ...


class UnavailableBackend:
    def classify(self, messages):
        raise BackendError("backend_unavailable")

    def generate(self, messages):
        raise BackendError("backend_unavailable")

    def metadata(self):
        return {"backend": "disabled", "model": "none", "options": OPTIONS}


class OllamaBackend:
    def __init__(self, url: str | None = None, model: str | None = None):
        self.url = (url or os.getenv("MANNSAHARA_OLLAMA_URL", "http://127.0.0.1:11435")).rstrip("/")
        self.model = model or os.getenv("MANNSAHARA_MODEL", "qwen2.5:1.5b")
        parsed = urlparse(self.url)
        # Keep fictional session content on this computer; remote providers require a code/config change.
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Only a local Ollama HTTP endpoint is supported")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Endpoint credentials, queries, and fragments are not supported")
        self.client = httpx.Client(trust_env=False)

    def _chat(self, messages, prompt_name, timeout, structured=False):
        prompt = (ROOT / "prompts" / prompt_name).read_text()
        options = dict(OPTIONS)
        if structured:
            options["num_predict"] = 24
        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": "30m",
            "options": options,
            "messages": [{"role": "system", "content": prompt}, *messages],
        }
        if structured:
            payload["format"] = SCHEMA
        try:
            response = self.client.post(f"{self.url}/api/chat", json=payload, timeout=timeout)
            response.raise_for_status()
            body = response.json()
            text = body["message"]["content"]
            if body.get("done") is not True or not isinstance(text, str) or len(text) > 4000:
                raise ValueError("incomplete_response")
            return text
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise BackendError("local_model_request_failed") from None

    def classify(self, messages):
        return self._chat(messages, "classifier.txt", 3.0, structured=True)

    def generate(self, messages):
        return self._chat(messages, "support.txt", 6.0)

    def metadata(self):
        result = {
            "backend": "ollama",
            "model": self.model,
            "options": OPTIONS,
            "classifier_num_predict": 24,
            "classifier_timeout_s": 3,
            "generation_timeout_s": 6,
        }
        try:
            version = self.client.get(f"{self.url}/api/version", timeout=3)
            version.raise_for_status()
            tags = self.client.get(f"{self.url}/api/tags", timeout=3)
            tags.raise_for_status()
            model = next(m for m in tags.json()["models"] if m["name"] == self.model)
            result.update(
                runtime_version=version.json()["version"],
                model_digest=model["digest"],
                model_details=model.get("details", {}),
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError, StopIteration):
            result["metadata_status"] = "unavailable"
        return result


def parse_label(raw: str):
    from .policy import Route

    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict) or set(obj) != {"route"} or not isinstance(obj["route"], str):
            raise ValueError
        route = Route(obj["route"])
        if route == Route.SAFE_FALLBACK:
            raise ValueError
        return route
    except (ValueError, TypeError):
        raise BackendError("invalid_classifier_output") from None
