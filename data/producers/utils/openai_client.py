# data/producers/utils/openai_client.py
from __future__ import annotations

import os
from functools import lru_cache
from openai import OpenAI

GMS_BASE_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1"


def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Producers용 GMS 기반 OpenAI 클라이언트 공통 유틸
    - .env: OPENAI_API_KEY 필수
    - base_url: 기본값은 SSAFY GMS 프록시
    """
    api_key = _require("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", GMS_BASE_URL)
    timeout = float(os.getenv("OPENAI_TIMEOUT", "30"))

    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
