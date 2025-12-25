# back-end/core/utils/openai_client.py
from __future__ import annotations

import os
from functools import lru_cache
from openai import OpenAI


def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    GMS 기반 공통 OpenAI 클라이언트 (SSAFY)
    """
    api_key = _require("OPENAI_API_KEY")

    # ✅ 기본은 GMS 프록시
    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://gms.ssafy.io/gmsapi/api.openai.com/v1",
    )
    timeout = float(os.getenv("OPENAI_TIMEOUT", "30"))

    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
