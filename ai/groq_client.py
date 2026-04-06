"""
Groq API client with exponential back-off, timeout handling,
rate-limit detection, and AI fallback responses.
"""
from __future__ import annotations

import time
import functools
from typing import Optional
import httpx

from groq import Groq, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError

from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT,
    MAX_RETRIES,
    BACKOFF_BASE,
)
from utils.logger import get_logger

log = get_logger(__name__)

_FALLBACK = (
    "⚠️ AI analysis is temporarily unavailable. "
    "Please check your GROQ_API_KEY in the .env file and try again."
)

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        # Bypassing the proxy bug by passing a vanilla httpx client
        _client = Groq(
            api_key=GROQ_API_KEY, 
            timeout=GROQ_TIMEOUT,
            http_client=httpx.Client()  # <-- ADD THIS LINE
        )
    return _client


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = GROQ_MODEL,
    max_tokens: int = GROQ_MAX_TOKENS,
    temperature: float = GROQ_TEMPERATURE,
) -> str:
    """
    Send a chat completion request to Groq with automatic retry.
    Returns the assistant's text response or a graceful fallback.
    """
    if not GROQ_API_KEY:
        log.warning("GROQ_API_KEY not set — returning fallback.")
        return _FALLBACK

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content or ""
            log.info(
                "Groq completion OK (attempt %d/%d, %d tokens used)",
                attempt,
                MAX_RETRIES,
                response.usage.total_tokens if response.usage else -1,
            )
            return text.strip()

        except RateLimitError as exc:
            delay = BACKOFF_BASE ** attempt
            log.warning(
                "Groq rate-limited (attempt %d/%d). Waiting %.1fs…",
                attempt, MAX_RETRIES, delay,
            )
            if attempt == MAX_RETRIES:
                return (
                    "⚠️ The AI assistant has hit its rate limit. "
                    "Please wait a moment and try again."
                )
            time.sleep(delay)

        except APITimeoutError:
            log.warning("Groq timeout (attempt %d/%d).", attempt, MAX_RETRIES)
            if attempt == MAX_RETRIES:
                return "⚠️ AI request timed out. Please try again."
            time.sleep(BACKOFF_BASE ** attempt)

        except APIConnectionError as exc:
            log.error("Groq connection error: %s", exc)
            return "⚠️ Could not connect to the AI service. Check your internet connection."

        except APIStatusError as exc:
            log.error("Groq API status error %s: %s", exc.status_code, exc.message)
            return f"⚠️ AI service error ({exc.status_code}). Please try again later."

        except Exception as exc:
            log.error("Unexpected Groq error (attempt %d): %s", attempt, exc)
            if attempt == MAX_RETRIES:
                return _FALLBACK
            time.sleep(BACKOFF_BASE ** attempt)

    return _FALLBACK


def stream_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = GROQ_MODEL,
    max_tokens: int = GROQ_MAX_TOKENS,
    temperature: float = GROQ_TEMPERATURE,
):
    """
    Generator that streams tokens from Groq.
    Falls back to a single yielded fallback string on error.
    """
    if not GROQ_API_KEY:
        yield _FALLBACK
        return

    try:
        client = _get_client()
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except RateLimitError:
        yield "\n\n⚠️ Rate limit reached. Please wait and try again."
    except APITimeoutError:
        yield "\n\n⚠️ Request timed out."
    except Exception as exc:
        log.error("Stream completion error: %s", exc)
        yield _FALLBACK
