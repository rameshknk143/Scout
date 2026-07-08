"""
Thin wrapper around OpenRouter's chat completions API (OpenAI-compatible
REST, plain requests.post() -- no SDK, consistent with the rest of this
codebase's dependency-light approach). Used for the one AI-dependent piece
of Scout: Phase 2.1's suggested listing copy.

Ram was explicit he didn't want to pay for a Claude/OpenAI key, and offered
a free-tier OpenRouter key instead, pointed at "openrouter/free" --
OpenRouter's own real router model that auto-selects among free models
("selects free models at random... filters for models that fit the task",
per OpenRouter's own model catalog description, verified via a live
GET /models call before building this, not assumed).

Every call here is optional and fails soft: if OPENROUTER_API_KEY isn't set,
or the call errors, times out, or the picked free model returns garbage,
callers get None back, never a crash or a fabricated suggestion. Free-tier
models are rate-limited and can be flaky -- Scout's rule-based features must
never depend on this being up.
"""

import os

import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"


def is_configured():
    return bool(OPENROUTER_API_KEY)


def chat(system_prompt, user_prompt, max_tokens=700, timeout=25):
    """Returns the model's text response, or None on any failure (key not
    set, network error, non-200, rate limit, malformed response)."""
    if not OPENROUTER_API_KEY:
        return None
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip() if content else None
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError):
        return None
