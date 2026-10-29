"""AI Task integration for Yandex AI Studio."""

import asyncio
import base64
from json import JSONDecodeError
import logging
from typing import override

import aiohttp

from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.json import json_loads

from .const import CONF_IMAGE_MODEL, DEFAULT_CHAT_MODEL, DEFAULT_IMAGE_MODEL
from .entity import YandexAIBaseLLMEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AI Task entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "ai_task_data":
            continue
        async_add_entities(
            [YandexAITaskEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class YandexAITaskEntity(ai_task.AITaskEntity, YandexAIBaseLLMEntity):
    """Yandex AI Studio AI Task entity."""

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the entity."""
        super().__init__(entry, subentry, DEFAULT_CHAT_MODEL)
        self._attr_supported_features = (
            ai_task.AITaskEntityFeature.GENERATE_DATA
            | ai_task.AITaskEntityFeature.GENERATE_IMAGE
        )

    @override
    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Handle a generate data task."""
        await self._async_handle_chat_log(chat_log, task.structure)

        if not chat_log.content or not isinstance(
            chat_log.content[-1], conversation.AssistantContent
        ):
            raise HomeAssistantError("Failed to get response from Yandex AI Studio")

        text = chat_log.content[-1].content or ""
        if not task.structure:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )

        try:
            data = json_loads(text)
        except JSONDecodeError as err:
            _LOGGER.error("Failed to parse JSON response: %s. Response: %s", err, text)
            raise HomeAssistantError("Failed to parse structured JSON response") from err

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data,
        )


    @override
    async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate image task via YandexART."""
        user_message = chat_log.content[-1]
        assert isinstance(user_message, conversation.UserContent)

        prompt = user_message.content
        image_model = self.subentry.data.get(CONF_IMAGE_MODEL, DEFAULT_IMAGE_MODEL)

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self.folder_id,
        }

        payload = {
            "modelUri": f"art://{self.folder_id}/{image_model}",
            "generationOptions": {"mimeType": "image/jpeg"},
            "messages": [{"weight": 1, "text": prompt}],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        raise HomeAssistantError(
                            f"Yandex ART Error ({resp.status}): {err}"
                        )

                    data = await resp.json()
                    operation_id = data.get("id")
                    if not operation_id:
                        raise HomeAssistantError("No operation ID returned")

                for _ in range(60):
                    await asyncio.sleep(1.0)
                    async with session.get(
                        f"https://llm.api.cloud.yandex.net/operations/{operation_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as poll_resp:
                        if poll_resp.status != 200:
                            err = await poll_resp.text()
                            raise HomeAssistantError(
                                f"Poll Error ({poll_resp.status}): {err}"
                            )

                        poll_data = await poll_resp.json()
                        if poll_data.get("done"):
                            if "error" in poll_data:
                                raise HomeAssistantError(
                                    f"Generation failed: {poll_data['error']}"
                                )

                            image_base64 = poll_data.get("response", {}).get("image")
                            if not image_base64:
                                raise HomeAssistantError("No image in response")

                            image_data = base64.b64decode(image_base64)
                            chat_log.async_add_assistant_content_without_tools(
                                conversation.AssistantContent(
                                    agent_id=self.entity_id,
                                    content="Изображение сгенерировано.",
                                )
                            )

                            return ai_task.GenImageTaskResult(
                                image_data=image_data,
                                conversation_id=chat_log.conversation_id,
                                mime_type="image/jpeg",
                                model=image_model.partition("/")[0],
                            )

                raise HomeAssistantError("Image generation timed out")

        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(f"Image generation error: {err}") from err

