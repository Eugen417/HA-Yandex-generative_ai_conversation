"""Shared API helpers for Yandex AI Studio (auth, models discovery, web search)."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_CHAT_MODEL

_LOGGER = logging.getLogger(__name__)

_IAM_TOKEN_RE = re.compile(r"^t\d\.")

CHAT_COMPLETIONS_URL = "https://llm.api.cloud.yandex.net/v1/chat/completions"
MODELS_LIST_URLS = (
    "https://llm.api.cloud.yandex.net/v1/models",
    "https://ai.api.cloud.yandex.net/v1/models",
)
GEN_SEARCH_URL = "https://searchapi.api.cloud.yandex.net/v2/gen/search"
RESPONSES_URL = "https://ai.api.cloud.yandex.net/v1/responses"


class YandexAuthError(Exception):
    """Raised when Yandex API rejects credentials or folder access."""


class YandexConnectionError(Exception):
    """Raised when Yandex API cannot be reached."""


def format_auth_header(raw_key: str) -> str:
    """Build Authorization header value supporting both Api-Key and IAM tokens."""
    clean_key = raw_key.strip()
    if clean_key.lower().startswith(("api-key ", "bearer ")):
        return clean_key
    if _IAM_TOKEN_RE.match(clean_key):
        return f"Bearer {clean_key}"
    return f"Api-Key {clean_key}"


def build_yandex_headers(
    api_key: str,
    folder_id: str,
    *,
    disable_data_logging: bool = True,
    include_content_type: bool = True,
) -> dict[str, str]:
    """Construct standard headers for Yandex AI Studio HTTP endpoints."""
    clean_folder = folder_id.strip()
    headers: dict[str, str] = {
        "Authorization": format_auth_header(api_key),
        "x-folder-id": clean_folder,
        "OpenAI-Project": clean_folder,
    }
    if include_content_type:
        headers["Content-Type"] = "application/json"
    if disable_data_logging:
        headers["x-data-logging-enabled"] = "false"
    return headers


def build_model_uri(folder_id: str, model_name: str, prefix: str = "gpt") -> str:
    """Build full Yandex model URI (e.g. gpt://<folder_id>/yandexgpt/latest)."""
    clean_model = model_name.strip()
    if "://" in clean_model:
        return clean_model
    clean_folder = folder_id.strip()
    if prefix == "gpt" and "/" not in clean_model:
        clean_model = f"{clean_model}/latest"
    return f"{prefix}://{clean_folder}/{clean_model}"


async def async_validate_credentials_and_fetch_models(
    hass: HomeAssistant,
    api_key: str,
    folder_id: str,
    *,
    disable_data_logging: bool = True,
) -> list[str]:
    """Validate credentials against Yandex AI Studio /v1/models and return model IDs."""
    clean_key = api_key.strip()
    clean_folder = folder_id.strip()
    if not clean_key or not clean_folder:
        raise YandexAuthError("Empty API key or Folder ID")

    headers = build_yandex_headers(
        clean_key,
        clean_folder,
        disable_data_logging=disable_data_logging,
        include_content_type=False,
    )
    session = async_get_clientsession(hass)
    last_err: Exception | None = None

    for url in MODELS_LIST_URLS:
        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (401, 403):
                    body = await resp.text()
                    _LOGGER.warning(
                        "Yandex AI Studio auth check failed (%s): %s",
                        resp.status,
                        body[:200],
                    )
                    raise YandexAuthError(f"HTTP {resp.status}")
                if resp.status == 200:
                    payload = await resp.json()
                    raw_items = payload.get("data", [])
                    models: list[str] = []
                    if isinstance(raw_items, list):
                        for item in raw_items:
                            if isinstance(item, dict) and isinstance(
                                mid := item.get("id"), str
                            ):
                                models.append(mid)
                    return models
                body = await resp.text()
                _LOGGER.debug(
                    "Models endpoint %s returned HTTP %s: %s",
                    url,
                    resp.status,
                    body[:200],
                )
        except YandexAuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            last_err = err
            _LOGGER.debug("Error connecting to %s: %s", url, err)

    if last_err is not None:
        raise YandexConnectionError(str(last_err)) from last_err
    return []


def normalize_discovered_models(
    raw_model_ids: list[str],
    folder_id: str,
    prefix: str = "gpt",
) -> list[str]:
    """Extract short model names from discovered Yandex model URIs."""
    clean_folder = folder_id.strip()
    folder_prefix = f"{prefix}://{clean_folder}/"
    generic_prefix = f"{prefix}://"
    normalized: list[str] = []

    for mid in raw_model_ids:
        if not mid.startswith(generic_prefix):
            continue
        if mid.startswith(folder_prefix):
            short = mid.removeprefix(folder_prefix)
        else:
            parts = mid.removeprefix(generic_prefix).split("/", 1)
            short = parts[1] if len(parts) == 2 and parts[0] == clean_folder else mid
        if short and short not in normalized:
            normalized.append(short)
    return normalized


def _parse_gen_search_payload(raw_text: str) -> tuple[str, list[dict[str, str]]]:
    """Parse JSON or NDJSON stream returned by /v2/gen/search."""
    text_answer = ""
    sources: list[dict[str, str]] = []
    chunks: list[Any] = []
    stripped = raw_text.strip()
    if not stripped:
        return "", []

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            chunks.extend(parsed)
        else:
            chunks.append(parsed)
    except json.JSONDecodeError:
        for line in stripped.splitlines():
            if line := line.strip():
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    for item in chunks:
        if not isinstance(item, dict):
            continue
        node = item.get("result", item)
        if not isinstance(node, dict):
            continue
        msg = node.get("message")
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            text_answer = msg["content"].strip()
        raw_sources = node.get("sources")
        if isinstance(raw_sources, list):
            collected: list[dict[str, str]] = []
            for src in raw_sources:
                if not isinstance(src, dict):
                    continue
                url = str(src.get("url") or "").strip()
                title = str(src.get("title") or "").strip()
                if url and (src.get("used", True) or len(collected) < 5):
                    collected.append({"title": title or url, "url": url})
            if collected:
                sources = collected

    return text_answer, sources


async def async_yandex_web_search(
    hass: HomeAssistant,
    *,
    api_key: str,
    folder_id: str,
    query: str,
    model_name: str = DEFAULT_CHAT_MODEL,
    disable_data_logging: bool = True,
) -> dict[str, Any]:
    """Execute Yandex Web Search via Search API v2 (/v2/gen/search) with /v1/responses fallback."""
    clean_query = query.strip()
    if not clean_query:
        return {"error": "Empty search query"}

    session = async_get_clientsession(hass)
    headers = build_yandex_headers(
        api_key,
        folder_id,
        disable_data_logging=disable_data_logging,
    )
    gen_payload = {
        "folderId": folder_id.strip(),
        "messages": [{"content": clean_query, "role": "ROLE_USER"}],
        "fixMisspell": True,
    }
    gen_status: int | None = None
    gen_err_text = ""

    try:
        async with session.post(
            GEN_SEARCH_URL,
            headers=headers,
            json=gen_payload,
            timeout=aiohttp.ClientTimeout(total=35),
        ) as resp:
            raw_body = await resp.text()
            gen_status = resp.status
            if resp.status == 200:
                answer, sources = _parse_gen_search_payload(raw_body)
                if answer:
                    return {
                        "answer": answer,
                        "sources": sources[:6],
                        "provider": "yandex_gen_search",
                    }
            else:
                gen_err_text = raw_body[:300]
                _LOGGER.debug(
                    "Yandex GenSearch HTTP %s: %s", resp.status, gen_err_text
                )
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        gen_err_text = str(err)
        _LOGGER.debug("Yandex GenSearch request error: %s", err)

    responses_payload = {
        "model": build_model_uri(folder_id, model_name, "gpt"),
        "input": clean_query,
        "tools": [{"type": "web_search"}],
    }
    try:
        async with session.post(
            RESPONSES_URL,
            headers=headers,
            json=responses_payload,
            timeout=aiohttp.ClientTimeout(total=40),
        ) as resp:
            if resp.status == 200:
                res_json = await resp.json()
                output_text = str(res_json.get("output_text") or "").strip()
                sources_list: list[dict[str, str]] = []
                for out_item in res_json.get("output", []) or []:
                    if not isinstance(out_item, dict):
                        continue
                    for part in out_item.get("content", []) or []:
                        if not isinstance(part, dict):
                            continue
                        if not output_text and isinstance(part.get("text"), str):
                            output_text = part["text"].strip()
                        for ann in part.get("annotations", []) or []:
                            if isinstance(ann, dict) and ann.get("url"):
                                sources_list.append(
                                    {
                                        "title": str(ann.get("title") or ann["url"]),
                                        "url": str(ann["url"]),
                                    }
                                )
                if output_text:
                    return {
                        "answer": output_text,
                        "sources": sources_list[:6],
                        "provider": "yandex_responses_web_search",
                    }
            else:
                _LOGGER.debug(
                    "Yandex Responses fallback HTTP %s: %s",
                    resp.status,
                    (await resp.text())[:300],
                )
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        _LOGGER.debug("Yandex Responses fallback error: %s", err)

    if gen_status in (401, 403):
        return {
            "error": (
                "Нет доступа к Yandex Search API (HTTP 403). "
                "Назначьте сервисному аккаунту в Yandex Cloud роль "
                "'search-api.webSearch.user' (или 'ai.editor')."
            )
        }
    return {
        "error": f"Не удалось выполнить поиск Yandex Search ({gen_status or 'timeout'}): {gen_err_text}"
    }


