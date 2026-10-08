"""Minimal Groq (OpenAI-compatible) client with a per-(key, model) token-rate limiter.

- Keys are read from environment variables only and are never printed or logged.
- Groq free tier (as observed on this account): 8,000 tokens/min and ~200K tokens/day
  per model. Cached prompt tokens do not count toward limits (Groq prompt-caching docs),
  so the limiter only counts uncached prompt tokens + completion tokens.
"""
import os, time, threading, json, random
import requests

API = "https://api.groq.com/openai/v1/chat/completions"


class Limiter:
    def __init__(self, tpm=7000):
        self.tpm = tpm
        self.events = []  # (timestamp, tokens)
        self.lock = threading.Lock()

    def _used(self, now):
        self.events = [(t, n) for t, n in self.events if now - t < 60]
        return sum(n for _, n in self.events)

    def wait(self, est):
        while True:
            with self.lock:
                now = time.time()
                if self._used(now) + est <= self.tpm:
                    self.events.append((now, est))  # provisional reservation
                    return now
            time.sleep(1.0)

    def settle(self, stamp, est, actual):
        with self.lock:
            for i, (t, n) in enumerate(self.events):
                if t == stamp and n == est:
                    self.events[i] = (t, actual)
                    break


_limiters = {}
_lock = threading.Lock()
USAGE = {}  # (env_name, model) -> dict of token counts


def _limiter(env, model, tpm):
    with _lock:
        k = (env, model)
        if k not in _limiters:
            _limiters[k] = Limiter(tpm)
        return _limiters[k]


def chat(messages, model, key_env="GROQ_API_KEY", tools=None, tool_choice=None,
         temperature=0.3, max_tokens=800, reasoning_effort=None, response_format=None,
         est_tokens=1500, tpm=7000, retries=8):
    key = os.environ.get(key_env)
    if not key:
        raise RuntimeError(f"env var {key_env} is not set")
    body = {"model": model, "messages": messages, "temperature": temperature,
            "max_completion_tokens": max_tokens}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice or "auto"
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    if response_format:
        body["response_format"] = response_format
    lim = _limiter(key_env, model, tpm)
    for attempt in range(retries):
        stamp = lim.wait(est_tokens)
        try:
            r = requests.post(API, headers={"Authorization": f"Bearer {key}",
                                            "Content-Type": "application/json"},
                              json=body, timeout=120)
        except requests.RequestException as e:
            lim.settle(stamp, est_tokens, 0)
            time.sleep(3 + attempt * 2)
            continue
        if r.status_code == 429:
            lim.settle(stamp, est_tokens, est_tokens)
            ra = r.headers.get("retry-after")
            msg = r.text[:300]
            if "tokens per day" in msg or "TPD" in msg:
                raise RuntimeError(f"DAILY_LIMIT {key_env}/{model}: {msg}")
            time.sleep(float(ra) + 1 if ra else 10 + attempt * 5)
            continue
        if r.status_code >= 500:
            lim.settle(stamp, est_tokens, 0)
            time.sleep(5 + attempt * 3)
            continue
        if r.status_code != 200:
            lim.settle(stamp, est_tokens, 0)
            # tool-call generation failures on Groq come back as 400; retry a few times
            if r.status_code == 400 and attempt < retries - 1 and "tool" in r.text.lower():
                time.sleep(2)
                continue
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        u = data.get("usage", {})
        cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
        uncached = u.get("prompt_tokens", 0) - cached + u.get("completion_tokens", 0)
        lim.settle(stamp, est_tokens, uncached)
        with _lock:
            d = USAGE.setdefault(f"{key_env}|{model}", {"calls": 0, "prompt": 0, "cached": 0, "completion": 0})
            d["calls"] += 1
            d["prompt"] += u.get("prompt_tokens", 0)
            d["cached"] += cached
            d["completion"] += u.get("completion_tokens", 0)
        return data["choices"][0]["message"], u
    raise RuntimeError(f"giving up after {retries} attempts ({key_env}/{model})")
