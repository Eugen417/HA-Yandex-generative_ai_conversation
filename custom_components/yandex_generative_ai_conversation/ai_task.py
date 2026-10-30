"""AI Task integration for Yandex AI Studio."""

import asyncio
import base64
from json import JSONDecodeError
import logging
from typing import Any, override

import aiohttp

from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.json import json_loads

from .const import (
    CONF_IMAGE_MODEL,
    CONF_RECOMMENDED,
    DEFAULT_CHAT_MODEL,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_VISION_MODEL,
    DOMAIN,
)
from .entity import YandexAIBaseLLMEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AI Task entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type not in ("ai_task_data", "ai_task_image"):
            continue
        async_add_entities(
            [YandexAITaskEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class YandexAITaskEntity(ai_task.AITaskEntity, YandexAIBaseLLMEntity):
    """Yandex AI Studio AI Task entity."""

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the entity."""
        default_model = (
            DEFAULT_IMAGE_MODEL
            if subentry.subentry_type == "ai_task_image"
            else DEFAULT_CHAT_MODEL
        )
        super().__init__(entry, subentry, default_model)
        if subentry.subentry_type == "ai_task_image":
            self._attr_supported_features = ai_task.AITaskEntityFeature.GENERATE_IMAGE
        else:
            self._attr_supported_features = (
                ai_task.AITaskEntityFeature.GENERATE_DATA
                | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
            )

    @override
    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Handle a generate data task (including multimodal image/camera analysis)."""
        last_msg = chat_log.content[-1] if chat_log.content else None
        if (
            isinstance(last_msg, conversation.UserContent)
            and getattr(last_msg, "attachments", None)
        ):
            text = await self._async_analyze_attachments(last_msg, chat_log)
        else:
            await self._async_handle_chat_log(chat_log, task.structure)
            if not chat_log.content or not isinstance(
                chat_log.content[-1], conversation.AssistantContent
            ):
                raise HomeAssistantError("Failed to get response from Yandex AI Studio")
            text = (chat_log.content[-1].content or "").strip()
        if not task.structure:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )

        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            data = json_loads(text)
        except JSONDecodeError as err:
            _LOGGER.error("Failed to parse JSON response: %s. Response: %s", err, text)
            raise HomeAssistantError("Failed to parse structured JSON response") from err

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data,
        )

    async def _async_analyze_attachments(
        self,
        user_message: conversation.UserContent,
        chat_log: conversation.ChatLog,
    ) -> str:
        """Analyze image/camera attachments using Yandex AI Studio Vision model (Gemma 3 27B)."""
        content_parts: list[dict[str, Any]] = [
            {"type": "text", "text": user_message.content or "Опиши это изображение."}
        ]
        for attachment in user_message.attachments or []:
            if not str(attachment.mime_type).startswith("image/"):
                raise HomeAssistantError(
                    f"Поддерживаются только изображения (получен {attachment.mime_type})"
                )
            img_bytes = await self.hass.async_add_executor_job(
                attachment.path.read_bytes
            )
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{attachment.mime_type};base64,{b64_img}"},
                }
            )

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Project": self.folder_id,
        }

        vision_candidates = [
            f"gpt://{self.folder_id}/{DEFAULT_VISION_MODEL}",
            f"gpt://{self.folder_id}/gemma-3-27b-it",
            f"gpt://{self.folder_id}/qwen3.6-35b-a3b/latest",
            f"gpt://{self.folder_id}/qwen3.6-35b-a3b",
            f"gpt://{self.folder_id}/qwen2.5-vl-32b-instruct/latest",
            f"gpt://{self.folder_id}/qwen2.5-vl-32b-instruct",
            f"gpt://{self.folder_id}/aliceai-llm/latest",
        ]

        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        "https://ai.api.cloud.yandex.net/v1/models",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as models_resp:
                        if models_resp.status == 200:
                            models_json = await models_resp.json()
                            available_ids = [
                                str(m.get("id"))
                                for m in models_json.get("data", [])
                                if m.get("id")
                            ]
                            _LOGGER.info(
                                "Yandex AI Studio available /v1/models: %s",
                                available_ids,
                            )
                            for mid in available_ids:
                                if any(
                                    k in mid.lower()
                                    for k in ("vl", "vision", "gemma", "qwen3.6")
                                ) and mid not in vision_candidates:
                                    vision_candidates.insert(0, mid)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Failed to query /v1/models: %s", err)
                last_status = 0
                last_err = ""
                res_data: dict[str, Any] | None = None
                used_model = DEFAULT_VISION_MODEL

                for candidate_uri in vision_candidates:
                    payload = {
                        "model": candidate_uri,
                        "messages": [{"role": "user", "content": content_parts}],
                        "stream": False,
                    }
                    async with session.post(
                        "https://ai.api.cloud.yandex.net/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as resp:
                        if resp.status == 200:
                            res_data = await resp.json()
                            used_model = candidate_uri.removeprefix(
                                f"gpt://{self.folder_id}/"
                            )
                            break
                        last_status = resp.status
                        last_err = await resp.text()
                        _LOGGER.debug(
                            "Vision candidate %s returned %s: %s",
                            candidate_uri,
                            last_status,
                            last_err,
                        )

                if res_data is None:
                    raise HomeAssistantError(
                        f"Yandex Vision Error ({last_status}): {last_err}"
                    )

                choices = res_data.get("choices", [])
                if not choices:
                    raise HomeAssistantError("Пустой ответ от Yandex Vision")
                reply_text = (
                    choices[0].get("message", {}).get("content") or ""
                ).strip()

                usage = res_data.get("usage", {})
                in_tokens = int(usage.get("prompt_tokens", 0) or 0)
                out_tokens = int(usage.get("completion_tokens", 0) or 0)
                tot_tokens = int(
                    usage.get("total_tokens", 0) or (in_tokens + out_tokens)
                )
                if self.hass is not None and tot_tokens:
                    async_dispatcher_send(
                        self.hass,
                        f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                        {
                            "tokens": tot_tokens,
                            "input_tokens": in_tokens,
                            "output_tokens": out_tokens,
                            "cost_rub": tot_tokens * 0.40 / 1000.0,
                            "model": used_model,
                        },
                    )

                chat_log.async_add_assistant_content_without_tools(
                    conversation.AssistantContent(
                        agent_id=self.entity_id,
                        content=reply_text,
                    )
                )
                return reply_text
        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(f"Vision analysis error: {err}") from err



    @override
    async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate image task via Yandex AI Studio Images API (Alice AI ART)."""
        user_message = chat_log.content[-1]
        assert isinstance(user_message, conversation.UserContent)

        prompt = user_message.content.strip()
        if len(prompt) > 500:
            cut = prompt[:499].rsplit(" ", 1)[0]
            prompt = f"{cut or prompt[:499]}…"

        if self.subentry.data.get(CONF_RECOMMENDED):
            image_model = DEFAULT_IMAGE_MODEL
        else:
            image_model = str(
                self.subentry.data.get(CONF_IMAGE_MODEL, DEFAULT_IMAGE_MODEL)
            ).strip()
        if not image_model or image_model.startswith("yandex-art"):
            image_model = DEFAULT_IMAGE_MODEL

        model_uri = (
            image_model
            if image_model.startswith("art://")
            else f"art://{self.folder_id}/{image_model}"
        )

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Project": self.folder_id,
            "x-folder-id": self.folder_id,
        }

        payload = {
            "model": model_uri,
            "prompt": prompt,
            "size": "1024x1024",
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://ai.api.cloud.yandex.net/v1/images/generations",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp,
            ):
                if resp.status != 200:
                    err = await resp.text()
                    raise HomeAssistantError(
                        f"Alice AI ART Error ({resp.status}): {err}"
                    )

                res_data = await resp.json()
                items = res_data.get("data", [])
                if not items or not items[0].get("b64_json"):
                    raise HomeAssistantError(
                        "Alice AI ART не вернул изображение в поле data[0].b64_json"
                    )

                image_data = base64.b64decode(items[0]["b64_json"])
                mime_type = (
                    "image/jpeg"
                    if image_data.startswith(b"\xff\xd8")
                    else "image/png"
                )

                if self.hass is not None:
                    async_dispatcher_send(
                        self.hass,
                        f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                        {
                            "images": 1,
                            "cost_rub": 2.23,
                            "model": image_model,
                        },
                    )

                chat_log.async_add_assistant_content_without_tools(
                    conversation.AssistantContent(
                        agent_id=self.entity_id,
                        content="Изображение сгенерировано.",
                    )
                )

                return ai_task.GenImageTaskResult(
                    image_data=image_data,
                    conversation_id=chat_log.conversation_id,
                    mime_type=mime_type,
                    model=image_model.partition("/")[0],
                )

        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(f"Image generation error: {err}") from err


