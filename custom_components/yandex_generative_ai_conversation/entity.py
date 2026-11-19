"""Base entity for the Yandex AI Studio integration."""

from __future__ import annotations

import asyncio
import base64
from collections.abc import AsyncGenerator, Callable
from dataclasses import fields
import json
import logging
from typing import Any

import aiohttp

try:
    import probatio
except ImportError:
    probatio = None  # type: ignore[assignment]

try:
    import voluptuous_openapi
except ImportError:
    voluptuous_openapi = None  # type: ignore[assignment]

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, llm
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.json import json_dumps

from .const import (
    CONF_API_KEY,
    CONF_CHAT_MODEL,
    CONF_DISABLE_DATA_LOGGING,
    CONF_FOLDER_ID,
    CONF_IMAGE_MODEL,
    CONF_IMAGE_SEARCH,
    CONF_MAX_TOKENS,
    CONF_REASONING_EFFORT,
    CONF_RECOMMENDED,
    CONF_STREAMING,
    CONF_STT_MODEL,
    CONF_TEMPERATURE,
    CONF_TTS_VOICE,
    CONF_WEB_SEARCH,
    DEFAULT_CHAT_MODEL,
    DEFAULT_DISABLE_DATA_LOGGING,
    DEFAULT_IMAGE_SEARCH,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_STREAMING,
    DEFAULT_VISION_MODEL,
    DEFAULT_WEB_SEARCH,
    DOMAIN,
    MODEL_TOKEN_RATES_PER_1K,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    WEB_SEARCH_COST_RUB,
)
from .helpers import (
    CHAT_COMPLETIONS_URL,
    async_load_image_source,
    async_yandex_image_search,
    async_yandex_web_search,
    build_model_uri,
    build_yandex_headers,
    extract_inline_image_tags,
)

_LOGGER = logging.getLogger(__name__)
MAX_TOOL_ITERATIONS = 10
WEB_SEARCH_TOOL_NAME = "yandex_web_search"
IMAGE_SEARCH_TOOL_NAME = "yandex_image_search"
INTERNAL_SEARCH_TOOLS = {WEB_SEARCH_TOOL_NAME, IMAGE_SEARCH_TOOL_NAME}

_SUPPORTS_THINKING_CONTENT = any(
    f.name == "thinking_content" for f in fields(conversation.AssistantContent)
)

WEB_SEARCH_TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": WEB_SEARCH_TOOL_NAME,
        "description": (
            "Search the internet via Yandex Search for up-to-date information: "
            "current news, weather forecasts, exchange rates, schedules, prices, "
            "facts, events, and any real-time web data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Concise search query in Russian or English",
                }
            },
            "required": ["query"],
        },
    },
}

IMAGE_SEARCH_TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": IMAGE_SEARCH_TOOL_NAME,
        "description": (
            "Reverse image search via Yandex Smart Camera (Yandex Images CBIR) for "
            "the user's attached photo: identifies exact products, models, plants, "
            "parts, landmarks, brands, and returns matching web pages and store links."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": "Optional website domain filter (leave empty for all sites)",
                }
            },
        },
    },
}

WEB_SEARCH_SYSTEM_HINT = (
    "\nТебе доступен инструмент поиска в интернете `yandex_web_search`. "
    "Вызывай его для проверки актуальных новостей, курсов валют, погоды, цен и фактов."
)

IMAGE_SEARCH_SYSTEM_HINT = (
    "\nТебе доступен инструмент поиска по картинке `yandex_image_search` (Яндекс Картинки). "
    "Вызывай его, когда пользователь прислал фото и просит опознать товар, модель, "
    "растение, деталь, место или найти, где это купить."
)


class _ToolCallsBuffer:
    """Reconstruct streamed tool_calls chunks by index (aligned with yandex-ai-studio-sdk)."""

    def __init__(self) -> None:
        self._items: dict[int, dict[str, Any]] = {}

    def update(self, tool_calls_delta: list[dict[str, Any]]) -> None:
        """Append streamed tool call delta fragments."""
        for delta in tool_calls_delta:
            if not isinstance(delta, dict):
                continue
            raw_idx = delta.get("index", 0)
            idx = int(raw_idx) if isinstance(raw_idx, int) else 0
            entry = self._items.setdefault(
                idx,
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                },
            )
            if call_id := delta.get("id"):
                entry["id"] = str(call_id)
            if call_type := delta.get("type"):
                entry["type"] = str(call_type)
            if isinstance(fn := delta.get("function"), dict):
                if fn_name := fn.get("name"):
                    entry["function"]["name"] += str(fn_name)
                if fn_args := fn.get("arguments"):
                    entry["function"]["arguments"] += str(fn_args)

    def build(self) -> list[dict[str, Any]]:
        """Return ordered list of reconstructed tool call dicts."""
        result: list[dict[str, Any]] = []
        for idx, item in sorted(self._items.items()):
            fn_name = item["function"]["name"]
            if not fn_name:
                continue
            if not item["id"]:
                item["id"] = f"call_{idx}_{fn_name}"
            result.append(item)
        return result


def estimate_model_cost_rub(
    model_name: str, input_tokens: int, output_tokens: int
) -> float:
    """Calculate estimated RUB cost using split input/output rates incl. VAT."""
    lowered = model_name.lower()
    for needle, in_rate, out_rate in MODEL_TOKEN_RATES_PER_1K:
        if needle in lowered:
            return (input_tokens * in_rate + output_tokens * out_rate) / 1000.0
    return (input_tokens * 0.80 + output_tokens * 0.80) / 1000.0



def _normalize_yandex_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize JSON Schema for Yandex Foundation Models strict jsonSchema."""
    if not isinstance(schema, dict):
        return schema

    for key in (
        "default",
        "examples",
        "$comment",
        "deprecated",
        "readOnly",
        "writeOnly",
        "uniqueItems",
    ):
        schema.pop(key, None)

    if schema.get("format") in {
        "entity_id",
        "jinja2",
        "RFC 5646",
        "ISO 3166-1 alpha-2",
        "RGB",
    }:
        schema.pop("format", None)

    for def_key in ("$defs", "definitions"):
        if isinstance(defs := schema.get(def_key), dict):
            for v in defs.values():
                if isinstance(v, dict):
                    _normalize_yandex_json_schema(v)

    for list_key in ("anyOf", "oneOf", "allOf"):
        if isinstance(variants := schema.get(list_key), list):
            for variant in variants:
                if isinstance(variant, dict):
                    _normalize_yandex_json_schema(variant)

    if "properties" in schema and isinstance(schema["properties"], dict):
        schema["type"] = "object"
        schema["additionalProperties"] = False
        props = schema["properties"]
        schema["required"] = list(props.keys())
        for prop_schema in props.values():
            if isinstance(prop_schema, dict):
                _normalize_yandex_json_schema(prop_schema)

    if "items" in schema and isinstance(schema["items"], dict):
        _normalize_yandex_json_schema(schema["items"])

    return schema


def _schema_to_openapi(
    parameters: Any, custom_serializer: Callable[[Any], Any] | None
) -> dict[str, Any]:
    """Convert voluptuous/probatio schema to OpenAPI dict across HA 2025.7+ and 2026.9+."""
    if probatio is not None:
        return probatio.to_openapi(parameters, custom_serializer=custom_serializer)
    if voluptuous_openapi is not None:
        return voluptuous_openapi.convert(
            parameters, custom_serializer=custom_serializer
        )
    return {"type": "object", "properties": {}}


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> dict[str, Any]:
    """Format tool specification for Yandex OpenAI-compatible Chat Completions API."""
    schema: dict[str, Any] = {"type": "object", "properties": {}}
    if probatio is not None or voluptuous_openapi is not None:
        try:
            schema = _schema_to_openapi(tool.parameters, custom_serializer)
            if "type" not in schema or not isinstance(schema["type"], str):
                schema["type"] = "object"
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to convert tool schema for %s: %s", tool.name, err)
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


def _extract_tool_result_payload(
    content: conversation.ToolResultContent,
    *,
    compact_live_context: bool,
) -> dict[str, Any]:
    """Extract tool result dict compatibly across HA 2025.8+ and 2026.11+."""
    if compact_live_context and "GetLiveContext" in content.tool_name:
        return {"status": "ok"}
    if hasattr(content, "result"):
        return {
            "data": content.result.data,
            "error": content.result.error,
        }
    return {"data": content.tool_result}


async def _async_build_chat_messages(
    hass: HomeAssistant,
    chat_contents: list[conversation.Content],
    *,
    web_search_enabled: bool = False,
    image_search_enabled: bool = False,
) -> tuple[list[dict[str, Any]], bool, bytes | None]:
    """Convert ChatLog.content into OpenAI-compatible Yandex Chat messages."""
    messages: list[dict[str, Any]] = []
    has_images = False
    latest_image_bytes: bytes | None = None

    last_user_idx = 0
    for idx, item in enumerate(chat_contents):
        if isinstance(item, conversation.UserContent):
            last_user_idx = idx

    for idx, content in enumerate(chat_contents):
        if isinstance(content, conversation.SystemContent):
            sys_text = content.content or ""
            extra_hints = ""
            if web_search_enabled:
                extra_hints += WEB_SEARCH_SYSTEM_HINT
            if image_search_enabled:
                extra_hints += IMAGE_SEARCH_SYSTEM_HINT
            if extra_hints:
                sys_text = f"{sys_text}{extra_hints}".strip()
            if sys_text:
                messages.append({"role": "system", "content": sys_text})

        elif isinstance(content, conversation.UserContent):
            raw_text = content.content or ""
            cleaned_text, inline_sources = extract_inline_image_tags(raw_text)
            attachments = getattr(content, "attachments", None) or []
            image_attachments = [
                att
                for att in attachments
                if str(getattr(att, "mime_type", "")).startswith("image/")
            ]

            loaded_images: list[tuple[bytes, str]] = []
            for att in image_attachments:
                img_bytes = await hass.async_add_executor_job(att.path.read_bytes)
                loaded_images.append((img_bytes, str(att.mime_type)))

            if idx == last_user_idx:
                for src in inline_sources:
                    loaded = await async_load_image_source(hass, src)
                    if loaded is not None:
                        loaded_images.append(loaded)

            if loaded_images:
                has_images = True
                latest_image_bytes = loaded_images[-1][0]
                parts: list[dict[str, Any]] = [
                    {
                        "type": "text",
                        "text": cleaned_text or "Опиши это изображение и определи, что на нём.",
                    }
                ]
                for img_bytes, mime_str in loaded_images:
                    b64_str = base64.b64encode(img_bytes).decode("utf-8")
                    parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_str};base64,{b64_str}"},
                        }
                    )
                messages.append({"role": "user", "content": parts})
            else:
                messages.append({"role": "user", "content": cleaned_text or " "})

        elif isinstance(content, conversation.AssistantContent):
            if content.tool_calls:
                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.tool_name,
                                "arguments": json_dumps(tc.tool_args),
                            },
                        }
                        for tc in content.tool_calls
                    ],
                }
                if content.content:
                    assistant_msg["content"] = content.content
                messages.append(assistant_msg)
            else:
                messages.append(
                    {"role": "assistant", "content": content.content or " "}
                )

        elif isinstance(content, conversation.ToolResultContent):
            res_payload = _extract_tool_result_payload(
                content,
                compact_live_context=(idx < last_user_idx),
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": content.tool_call_id,
                    "content": json_dumps(res_payload),
                }
            )

    return messages, has_images, latest_image_bytes


class YandexAIBaseLLMEntity(Entity):
    """Yandex AI Studio base entity."""

    def __init__(
        self,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        default_model: str = DEFAULT_CHAT_MODEL,
    ) -> None:
        """Initialize the base entity."""
        self.entry = entry
        self._subentry = subentry
        self._subentry_id = subentry.subentry_id
        self.api_key = str(entry.data[CONF_API_KEY]).strip()
        self.folder_id = str(entry.data[CONF_FOLDER_ID]).strip()
        self.disable_data_logging = bool(
            entry.data.get(CONF_DISABLE_DATA_LOGGING, DEFAULT_DISABLE_DATA_LOGGING)
        )
        self.default_model = default_model
        self._attr_name = subentry.title
        self._attr_unique_id = subentry.subentry_id

        if subentry.data.get(CONF_RECOMMENDED):
            model = default_model
        elif subentry.subentry_type == "ai_task_image":
            model = subentry.data.get(CONF_IMAGE_MODEL) or default_model
        else:
            model = (
                subentry.data.get(CONF_CHAT_MODEL)
                or subentry.data.get(CONF_STT_MODEL)
                or subentry.data.get(CONF_TTS_VOICE)
                or subentry.data.get(CONF_IMAGE_MODEL)
                or default_model
            )
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Yandex",
            model=str(model),
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def subentry(self) -> ConfigSubentry:
        """Return the latest subentry from the config entry."""
        return self.entry.subentries.get(self._subentry_id, self._subentry)

    def _record_token_usage(
        self,
        model_name: str,
        in_tokens: int,
        out_tokens: int,
        tot_tokens: int,
    ) -> None:
        """Dispatch token and RUB cost metrics to diagnostic sensors."""
        if self.hass is None or tot_tokens <= 0:
            return
        cost_rub = estimate_model_cost_rub(model_name, in_tokens, out_tokens)
        async_dispatcher_send(
            self.hass,
            f"{DOMAIN}_usage_{self.subentry.subentry_id}",
            {
                "tokens": tot_tokens,
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "cost_rub": cost_rub,
                "model": model_name,
            },
        )

    @staticmethod
    def _parse_tool_arguments(raw_args: Any) -> dict[str, Any]:
        """Parse tool call arguments from JSON string or dict."""
        if isinstance(raw_args, dict):
            return raw_args
        if isinstance(raw_args, str) and raw_args.strip():
            try:
                parsed = json.loads(raw_args)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                _LOGGER.debug("Failed to decode tool JSON args: %s", raw_args)
        return {}

    async def _async_run_web_search_calls(
        self,
        search_calls: list[dict[str, Any]],
        model_name: str,
        latest_image_bytes: bytes | None = None,
    ) -> list[dict[str, Any]]:
        """Execute internal yandex_web_search / yandex_image_search tool calls."""
        tool_messages: list[dict[str, Any]] = []
        for call in search_calls:
            call_id = str(call.get("id") or "web_search_call")
            fn_obj = call.get("function") or {}
            fn_name = str(fn_obj.get("name") or WEB_SEARCH_TOOL_NAME)
            args = self._parse_tool_arguments(fn_obj.get("arguments"))

            if fn_name == IMAGE_SEARCH_TOOL_NAME:
                if not latest_image_bytes:
                    search_res: dict[str, Any] = {
                        "error": "No attached image found for reverse image search"
                    }
                else:
                    site = str(args.get("site") or "").strip()
                    _LOGGER.info("Yandex Image Search (CBIR) invoked: site=%r", site)
                    search_res = await async_yandex_image_search(
                        self.hass,
                        api_key=self.api_key,
                        folder_id=self.folder_id,
                        image_bytes=latest_image_bytes,
                        site=site,
                        disable_data_logging=self.disable_data_logging,
                    )
                    if self.hass is not None and "matches" in search_res:
                        async_dispatcher_send(
                            self.hass,
                            f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                            {
                                "tokens": 0,
                                "cost_rub": WEB_SEARCH_COST_RUB,
                                "model": f"{model_name} + image_search",
                            },
                        )
            else:
                query = str(args.get("query") or "").strip()
                _LOGGER.info("Yandex Web Search tool invoked: query=%r", query)
                search_res = await async_yandex_web_search(
                    self.hass,
                    api_key=self.api_key,
                    folder_id=self.folder_id,
                    query=query,
                    model_name=model_name,
                    disable_data_logging=self.disable_data_logging,
                )
                if self.hass is not None and "answer" in search_res:
                    async_dispatcher_send(
                        self.hass,
                        f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                        {
                            "tokens": 0,
                            "cost_rub": WEB_SEARCH_COST_RUB,
                            "model": f"{model_name} + web_search",
                        },
                    )

            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json_dumps(search_res),
                }
            )
        return tool_messages

    @staticmethod
    def _parse_sse_event_line(
        line: str,
        tool_buffer: _ToolCallsBuffer,
        usage_info: dict[str, int],
    ) -> tuple[bool, str | None, str | None]:
        """Parse one SSE line; returns (is_done, text_piece, thinking_piece)."""
        if not line or not line.startswith("data:"):
            return False, None, None
        data_str = line[5:].strip()
        if data_str.startswith("[DONE]"):
            return True, None, None
        try:
            event_data = json.loads(data_str)
        except json.JSONDecodeError:
            return False, None, None
        if not isinstance(event_data, dict):
            return False, None, None
        if err_obj := event_data.get("error"):
            raise HomeAssistantError(f"Ошибка потока Yandex API: {err_obj}")

        if isinstance(raw_usage := event_data.get("usage"), dict):
            usage_info["in"] = int(raw_usage.get("prompt_tokens", 0) or 0)
            usage_info["out"] = int(raw_usage.get("completion_tokens", 0) or 0)
            usage_info["tot"] = int(
                raw_usage.get("total_tokens", 0)
                or (usage_info["in"] + usage_info["out"])
            )

        choices = event_data.get("choices")
        if not isinstance(choices, list) or not choices:
            return False, None, None
        choice = choices[0]
        if not isinstance(choice, dict):
            return False, None, None
        delta = choice.get("delta") or {}
        if not isinstance(delta, dict):
            return False, None, None

        if isinstance(tc_delta := delta.get("tool_calls"), list):
            tool_buffer.update(tc_delta)

        text_piece = delta.get("content")
        thinking_piece = delta.get("reasoning_content")
        return (
            False,
            text_piece if isinstance(text_piece, str) and text_piece else None,
            thinking_piece
            if isinstance(thinking_piece, str) and thinking_piece
            else None,
        )

    async def _async_execute_stream_turn(
        self,
        session: aiohttp.ClientSession,
        headers: dict[str, str],
        payload: dict[str, Any],
        chat_log: conversation.ChatLog,
        model_name: str,
    ) -> tuple[list[dict[str, Any]], bool, str]:
        """Run one SSE streaming turn and stream deltas into ChatLog."""
        stream_payload = {**payload, "stream": True}
        async with session.post(
            CHAT_COMPLETIONS_URL,
            headers=headers,
            json=stream_payload,
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                _LOGGER.error("Yandex Chat API error %s: %s", resp.status, err_text)
                raise HomeAssistantError(
                    f"Ошибка API Yandex ({resp.status}): {err_text}"
                )

            tool_buffer = _ToolCallsBuffer()
            usage_info: dict[str, int] = {}
            collected_parts: list[str] = []
            internal_search_calls: list[dict[str, Any]] = []
            had_ha_tool_calls = False

            async def _delta_generator() -> AsyncGenerator[dict[str, Any]]:
                nonlocal had_ha_tool_calls
                started_msg = False
                byte_buf = b""
                done = False

                async for chunk_bytes in resp.content.iter_any():
                    if done:
                        break
                    byte_buf += chunk_bytes
                    while b"\n" in byte_buf:
                        raw_line, byte_buf = byte_buf.split(b"\n", 1)
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        is_done, text_piece, thinking_piece = self._parse_sse_event_line(
                            line, tool_buffer, usage_info
                        )
                        if is_done:
                            done = True
                            break
                        if thinking_piece and _SUPPORTS_THINKING_CONTENT:
                            if not started_msg:
                                started_msg = True
                                yield {"role": "assistant"}
                            yield {"thinking_content": thinking_piece}
                        if text_piece:
                            if not started_msg:
                                started_msg = True
                                yield {"role": "assistant"}
                            collected_parts.append(text_piece)
                            yield {"content": text_piece}

                ha_inputs: list[llm.ToolInput] = []
                for tc in tool_buffer.build():
                    fn_name = tc["function"]["name"]
                    if fn_name in INTERNAL_SEARCH_TOOLS:
                        internal_search_calls.append(tc)
                    else:
                        ha_inputs.append(
                            llm.ToolInput(
                                id=tc["id"],
                                tool_name=fn_name,
                                tool_args=self._parse_tool_arguments(
                                    tc["function"]["arguments"]
                                ),
                            )
                        )

                if ha_inputs and chat_log.llm_api is not None:
                    had_ha_tool_calls = True
                    if not started_msg:
                        started_msg = True
                        yield {"role": "assistant"}
                    yield {"tool_calls": ha_inputs}
                elif not started_msg and not internal_search_calls:
                    started_msg = True
                    yield {"role": "assistant"}
                    yield {"content": ""}

            async for _ in chat_log.async_add_delta_content_stream(
                self.entity_id, _delta_generator()  # type: ignore[arg-type]
            ):
                pass

            full_text = "".join(collected_parts)
            in_tok = usage_info.get("in", 0)
            out_tok = usage_info.get("out", 0)
            tot_tok = usage_info.get("tot", 0)
            if tot_tok <= 0 and (full_text or internal_search_calls or had_ha_tool_calls):
                in_tok = max(1, len(json_dumps(payload.get("messages", []))) // 4)
                out_tok = max(1, len(full_text) // 4)
                tot_tok = in_tok + out_tok
            self._record_token_usage(model_name, in_tok, out_tok, tot_tok)
            return internal_search_calls, had_ha_tool_calls, full_text

    async def _async_execute_non_stream_turn(
        self,
        session: aiohttp.ClientSession,
        headers: dict[str, str],
        payload: dict[str, Any],
        chat_log: conversation.ChatLog,
        model_name: str,
    ) -> tuple[list[dict[str, Any]], bool, str]:
        """Run one non-streaming completion turn against /v1/chat/completions."""
        req_payload = {**payload, "stream": False}
        async with session.post(
            CHAT_COMPLETIONS_URL,
            headers=headers,
            json=req_payload,
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                _LOGGER.error("Yandex Chat API error %s: %s", resp.status, err_text)
                raise HomeAssistantError(
                    f"Ошибка API Yandex ({resp.status}): {err_text}"
                )

            res_data = await resp.json()
            choices = res_data.get("choices") or []
            if not choices:
                raise HomeAssistantError("Пустой ответ от Yandex AI Studio")

            usage = res_data.get("usage") or {}
            in_tok = int(usage.get("prompt_tokens", 0) or 0)
            out_tok = int(usage.get("completion_tokens", 0) or 0)
            tot_tok = int(usage.get("total_tokens", 0) or (in_tok + out_tok))
            self._record_token_usage(model_name, in_tok, out_tok, tot_tok)

            message = choices[0].get("message") or {}
            text_content = str(message.get("content") or "")
            raw_tool_calls = message.get("tool_calls") or []

            internal_search_calls: list[dict[str, Any]] = []
            ha_inputs: list[llm.ToolInput] = []
            for idx, tc in enumerate(raw_tool_calls):
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function") or {}
                fn_name = str(fn.get("name") or "")
                if not fn_name:
                    continue
                call_id = str(tc.get("id") or f"call_{idx}_{fn_name}")
                if fn_name in INTERNAL_SEARCH_TOOLS:
                    internal_search_calls.append(
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": fn_name,
                                "arguments": fn.get("arguments")
                                if isinstance(fn.get("arguments"), str)
                                else json_dumps(fn.get("arguments") or {}),
                            },
                        }
                    )
                else:
                    ha_inputs.append(
                        llm.ToolInput(
                            id=call_id,
                            tool_name=fn_name,
                            tool_args=self._parse_tool_arguments(fn.get("arguments")),
                        )
                    )

            had_ha_tool_calls = bool(ha_inputs and chat_log.llm_api is not None)
            if had_ha_tool_calls or not internal_search_calls:
                assistant_kwargs: dict[str, Any] = {
                    "agent_id": self.entity_id,
                    "content": text_content or None,
                    "tool_calls": ha_inputs if had_ha_tool_calls else None,
                }
                if _SUPPORTS_THINKING_CONTENT and message.get("reasoning_content"):
                    assistant_kwargs["thinking_content"] = str(
                        message["reasoning_content"]
                    )
                assistant_content = conversation.AssistantContent(**assistant_kwargs)
                if had_ha_tool_calls:
                    async for _ in chat_log.async_add_assistant_content(
                        assistant_content
                    ):
                        pass
                else:
                    chat_log.async_add_assistant_content_without_tools(assistant_content)

            return internal_search_calls, had_ha_tool_calls, text_content

    async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure: Any | None = None,
    ) -> None:
        """Generate an answer for the chat log using Yandex /v1/chat/completions."""
        options = self.subentry.data
        web_search_enabled = bool(options.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH))
        image_search_enabled = bool(
            options.get(CONF_IMAGE_SEARCH, DEFAULT_IMAGE_SEARCH)
        )
        streaming_enabled = (
            self.subentry.subentry_type == "conversation"
            and structure is None
            and bool(options.get(CONF_STREAMING, DEFAULT_STREAMING))
        )

        if options.get(CONF_RECOMMENDED):
            model_name = self.default_model
            temperature = float(RECOMMENDED_TEMPERATURE)
            max_tokens = int(RECOMMENDED_MAX_TOKENS)
            reasoning_effort = DEFAULT_REASONING_EFFORT
        else:
            model_name = str(options.get(CONF_CHAT_MODEL, self.default_model))
            temperature = float(options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE))
            max_tokens = int(options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS))
            reasoning_effort = str(
                options.get(CONF_REASONING_EFFORT, DEFAULT_REASONING_EFFORT)
            ).lower()

        tools: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        if chat_log.llm_api:
            for tool in chat_log.llm_api.tools:
                if tool.name not in seen_names:
                    seen_names.add(tool.name)
                    tools.append(_format_tool(tool, chat_log.llm_api.custom_serializer))
        if web_search_enabled and WEB_SEARCH_TOOL_NAME not in seen_names:
            tools.append(WEB_SEARCH_TOOL_SPEC)

        headers = build_yandex_headers(
            self.api_key,
            self.folder_id,
            disable_data_logging=self.disable_data_logging,
        )
        internal_turn_messages: list[dict[str, Any]] = []
        replace_trailing_assistant = False

        for _iteration in range(MAX_TOOL_ITERATIONS):
            base_messages, has_images, latest_image_bytes = (
                await _async_build_chat_messages(
                    self.hass,
                    chat_log.content,
                    web_search_enabled=web_search_enabled,
                    image_search_enabled=image_search_enabled,
                )
            )
            if (
                replace_trailing_assistant
                and base_messages
                and base_messages[-1].get("role") == "assistant"
            ):
                base_messages.pop()
            messages = [*base_messages, *internal_turn_messages]

            effective_model = model_name
            if has_images and not any(
                tag in effective_model.lower()
                for tag in ("qwen3.6", "deepseek-v4.1", "gemma", "vl")
            ):
                effective_model = DEFAULT_VISION_MODEL

            turn_tools = list(tools)
            if (
                image_search_enabled
                and latest_image_bytes is not None
                and IMAGE_SEARCH_TOOL_NAME not in seen_names
            ):
                turn_tools.append(IMAGE_SEARCH_TOOL_SPEC)

            payload: dict[str, Any] = {
                "model": build_model_uri(self.folder_id, effective_model, "gpt"),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if reasoning_effort in ("low", "medium", "high"):
                payload["reasoning_effort"] = reasoning_effort
            if turn_tools:
                payload["tools"] = turn_tools

            if structure is not None and (
                probatio is not None or voluptuous_openapi is not None
            ):
                try:
                    schema = _schema_to_openapi(
                        structure,
                        chat_log.llm_api.custom_serializer
                        if chat_log.llm_api
                        else llm.selector_serializer,
                    )
                    payload["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "ha_structured_output",
                            "schema": _normalize_yandex_json_schema(schema),
                            "strict": True,
                        },
                    }
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Failed to build json_schema: %s", err)

            try:
                session = async_get_clientsession(self.hass)
                turn_fn = (
                    self._async_execute_stream_turn
                    if streaming_enabled
                    else self._async_execute_non_stream_turn
                )
                search_calls, had_ha_tools, spoken_text = await turn_fn(
                    session, headers, payload, chat_log, effective_model
                )
                if search_calls:
                    assistant_search_msg: dict[str, Any] = {
                        "role": "assistant",
                        "tool_calls": search_calls,
                    }
                    if spoken_text:
                        assistant_search_msg["content"] = spoken_text
                        if not had_ha_tools:
                            replace_trailing_assistant = True
                    search_results = await self._async_run_web_search_calls(
                        search_calls, effective_model, latest_image_bytes
                    )
                    internal_turn_messages.append(assistant_search_msg)
                    internal_turn_messages.extend(search_results)
                    continue
            except HomeAssistantError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.error("Error communicating with Yandex API: %s", err)
                raise HomeAssistantError(
                    f"Ошибка соединения с Yandex API: {err}"
                ) from err

            if not chat_log.unresponded_tool_results:
                break

