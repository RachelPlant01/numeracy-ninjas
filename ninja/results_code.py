"""Results codes: a pupil's whole assessment packed into one scrambled code.

The code holds the question seed, the skills and the pupil's answers and
times — not the questions themselves (the teacher's copy of the app rebuilds
those from the seed). Nothing is stored anywhere: the code *is* the result.

It's scrambled and signed with a key from the app's secrets, so pupils can't
read it or edit their score. This is to keep a class honest, not bank-grade
encryption. Changing the key makes every earlier code unreadable.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import zlib

VERSION = 1
_MAC_BYTES = 6


def _keystream(key: bytes, nonce: bytes, n: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:n]


def encode(payload: dict, key: str) -> str:
    """dict -> 'ABCDE FGHIJ …' (base32 letters and digits, in groups of 5)."""
    k = key.encode()
    raw = zlib.compress(json.dumps({"v": VERSION, **payload}, separators=(",", ":")).encode(), 9)
    nonce = os.urandom(4)
    body = nonce + bytes(a ^ b for a, b in zip(raw, _keystream(k, nonce, len(raw))))
    mac = hmac.new(k, body, hashlib.sha256).digest()[:_MAC_BYTES]
    text = base64.b32encode(body + mac).decode().rstrip("=")
    return " ".join(text[i:i + 5] for i in range(0, len(text), 5))


def decode(code: str, key: str) -> dict:
    """Inverse of `encode`. Raises ValueError if the code is mistyped,
    incomplete, edited or made with a different key."""
    text = "".join(ch for ch in (code or "").upper() if ch.isalnum())
    text = text.replace("0", "O").replace("1", "I").replace("8", "B")  # common misreadings
    try:
        blob = base64.b32decode(text + "=" * (-len(text) % 8))
    except Exception:
        raise ValueError("That isn't a complete results code — check it was copied in full.")
    k = key.encode()
    body, mac = blob[:-_MAC_BYTES], blob[-_MAC_BYTES:]
    if len(body) < 5 or not hmac.compare_digest(mac, hmac.new(k, body, hashlib.sha256).digest()[:_MAC_BYTES]):
        raise ValueError("That results code doesn't check out — it may be incomplete, mistyped or changed.")
    nonce, data = body[:4], body[4:]
    payload = json.loads(zlib.decompress(bytes(a ^ b for a, b in zip(data, _keystream(k, nonce, len(data))))))
    if payload.get("v") != VERSION:
        raise ValueError("That code was made by a different version of the app.")
    return payload
