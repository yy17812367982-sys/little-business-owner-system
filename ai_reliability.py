"""Bounded, user-safe handling for external AI requests."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any


@dataclass
class AIServiceUnavailable(RuntimeError):
    """A retryable AI failure whose public message contains no provider details."""

    code: str
    user_message: str
    last_error: str = ""

    def __str__(self) -> str:
        return self.user_message


def _looks_like_timeout(message: str) -> bool:
    normalized = message.lower()
    return any(
        marker in normalized
        for marker in ("timeout", "timed out", "deadline exceeded", "readtimeout")
    )


def request_ai_text(
    generate_content: Callable[..., Any],
    models: Iterable[str],
    prompt: str,
    config: Any,
    max_attempts: int = 3,
) -> str:
    """Try a bounded number of models and return the first non-empty response."""

    attempts = 0
    last_error = ""
    saw_timeout = False

    for model_name in models:
        if attempts >= max_attempts:
            break
        attempts += 1
        try:
            response = generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            response_text = getattr(response, "text", None)
            if response_text and str(response_text).strip():
                return str(response_text)
            last_error = f"Empty response from {model_name}"
        except Exception as exc:  # provider exceptions vary by transport/version
            last_error = f"{model_name}: {exc}"
            saw_timeout = saw_timeout or _looks_like_timeout(str(exc))

    if saw_timeout:
        raise AIServiceUnavailable(
            code="AI_TIMEOUT",
            user_message=(
                "The AI service did not respond in time. Your inputs are still saved; "
                "please retry in a moment."
            ),
            last_error=last_error,
        )

    raise AIServiceUnavailable(
        code="AI_UNAVAILABLE",
        user_message=(
            "The AI service is temporarily unavailable. Your inputs are still saved; "
            "please retry in a moment."
        ),
        last_error=last_error,
    )
