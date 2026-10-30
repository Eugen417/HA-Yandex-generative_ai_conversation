"""Base entity for the Yandex AI Studio integration."""

import asyncio
from collections.abc import Callable
import logging
from typing import Any

import aiohttp
import probatio

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, llm
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.json import json_dumps

from .const import (
    CONF_API_KEY,
    CONF_CHAT_MODEL,
    CONF_FOLDER_ID,
    CONF_IMAGE_MODEL,
    CONF_MAX_TOKENS,
    CONF_RECOMMENDED,
    CONF_STT_MODEL,
    CONF_TEMPERATURE,
    CONF_TTS_VOICE,
    DEFAULT_CHAT_MODEL,
    DOMAIN,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)
MAX_TOOL_ITERATIONS = 10


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


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> dict[str, Any]:
    """Format tool specification for Yandex Foundation Models API."""
    schema: dict[str, Any] = {"type": "object", "properties": {}}
    if probatio is not None:
        try:
            schema = probatio.to_openapi(
                tool.parameters, custom_serializer=custom_serializer
            )
            if "type" not in schema or not isinstance(schema["type"], str):
                schema["type"] = "object"
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to convert tool schema for %s: %s", tool.name, err)
    return {
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        }
    }


def _build_yandex_messages(
    chat_contents: list[conversation.Content],
) -> list[dict[str, Any]]:
    """Convert ChatLog.content into Yandex Foundation Models messages."""
    messages: list[dict[str, Any]] = []
    pending_tool_results: list[dict[str, Any]] = []

    def flush_tool_results() -> None:
        if pending_tool_results:
            messages.append(
                {
                    "role": "user",
                    "toolResultList": {"toolResults": list(pending_tool_results)},
                }
            )
            pending_tool_results.clear()

    for content in chat_contents:
        if isinstance(content, conversation.ToolResultContent):
            pending_tool_results.append(
                {
                    "functionResult": {
                        "name": content.tool_name,
                        "content": json_dumps(
                            {
                                "data": content.result.data,
                                "error": content.result.error,
                            }
                        ),
                    }
                }
            )
            continue

        flush_tool_results()

        if isinstance(content, conversation.SystemContent):
            if content.content:
                messages.append({"role": "system", "text": content.content})
        elif isinstance(content, conversation.UserContent):
            messages.append({"role": "user", "text": content.content or " "})
        elif isinstance(content, conversation.AssistantContent):
            if content.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "toolCallList": {
                            "toolCalls": [
                                {
                                    "functionCall": {
                                        "name": tc.tool_name,
                                        "arguments": tc.tool_args,
                                    }
                                }
                                for tc in content.tool_calls
                            ]
                        },
                    }
                )
            else:
                messages.append(
                    {"role": "assistant", "text": content.content or " "}
                )

    flush_tool_results()
    return messages

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
        self.api_key = entry.data[CONF_API_KEY]
        self.folder_id = entry.data[CONF_FOLDER_ID]
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

    async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure: Any | None = None,
    ) -> None:
        """Generate an answer for the chat log."""
        options = self.subentry.data
        if options.get(CONF_RECOMMENDED):
            model_name = self.default_model
            temperature = float(RECOMMENDED_TEMPERATURE)
            max_tokens = int(RECOMMENDED_MAX_TOKENS)
        else:
            model_name = options.get(CONF_CHAT_MODEL, self.default_model)
            temperature = float(options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE))
            max_tokens = int(options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS))

        if (
            self.subentry.subentry_type == "conversation"
            and chat_log.llm_api
            and str(model_name).startswith("yandexgpt-lite")
        ):
            model_name = DEFAULT_CHAT_MODEL

        tools: list[dict[str, Any]] | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self.folder_id,
        }

        for _iteration in range(MAX_TOOL_ITERATIONS):
            messages = _build_yandex_messages(chat_log.content)
            payload: dict[str, Any] = {
                "modelUri": f"gpt://{self.folder_id}/{model_name}",
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": max_tokens,
                },
                "messages": messages,
            }
            if tools:
                payload["tools"] = tools

            if structure is not None and probatio is not None:
                try:
                    schema = probatio.to_openapi(
                        structure,
                        custom_serializer=(
                            chat_log.llm_api.custom_serializer
                            if chat_log.llm_api
                            else llm.selector_serializer
                        ),
                    )
                    payload["jsonSchema"] = {
                        "schema": _normalize_yandex_json_schema(schema)
                    }
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Failed to build jsonSchema: %s", err)

            try:
                async with (
                    aiohttp.ClientSession() as session,
                    session.post(
                        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=45),
                    ) as resp,
                ):
                    if resp.status != 200:
                        err_text = await resp.text()
                        _LOGGER.error("Yandex API error %s: %s", resp.status, err_text)
                        raise HomeAssistantError(
                            f"Ошибка API Yandex ({resp.status}): {err_text}"
                        )

                    res_data = await resp.json()
                    result_block = res_data.get("result", {})
                    alternatives = result_block.get("alternatives", [])
                    if not alternatives:
                        raise HomeAssistantError("Пустой ответ от Yandex GPT")

                    usage = result_block.get("usage", {})
                    in_tokens = int(usage.get("inputTextTokens", 0) or 0)
                    out_tokens = int(usage.get("completionTokens", 0) or 0)
                    tot_tokens = int(
                        usage.get("totalTokens", 0) or (in_tokens + out_tokens)
                    )
                    if "lite" in model_name:
                        rate_per_1k = 0.20
                    elif "aliceai" in model_name or "qwen" in model_name:
                        rate_per_1k = 0.50
                    else:
                        rate_per_1k = 1.20
                    cost_rub = tot_tokens * rate_per_1k / 1000.0
                    if self.hass is not None:
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

                    message = alternatives[0].get("message", {})
                    tool_calls = [
                        llm.ToolInput(
                            tool_name=tc["functionCall"]["name"],
                            tool_args=tc["functionCall"].get("arguments", {}),
                        )
                        for tc in message.get("toolCallList", {}).get("toolCalls", [])
                        if "functionCall" in tc
                    ]

                    assistant_content = conversation.AssistantContent(
                        agent_id=self.entity_id,
                        content=message.get("text") or None,
                        tool_calls=tool_calls or None,
                    )
                    _LOGGER.info(
                        "Yandex LLM [%s] tokens=%s tool_calls=%s text=%s",
                        model_name,
                        tot_tokens,
                        [tc.tool_name for tc in tool_calls],
                        (message.get("text") or "")[:120],
                    )
                    async for _ in chat_log.async_add_assistant_content(
                        assistant_content
                    ):
                        pass

            except HomeAssistantError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.error("Error communicating with Yandex API: %s", err)
                raise HomeAssistantError(
                    f"Ошибка соединения с Yandex API: {err}"
                ) from err

            if not chat_log.unresponded_tool_results:
                break

