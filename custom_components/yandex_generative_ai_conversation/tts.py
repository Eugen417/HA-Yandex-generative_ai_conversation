"""Text to speech support for Yandex AI Studio."""

from collections.abc import Mapping
import logging
from typing import Any

import aiohttp

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_TTS_EMOTION,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_TTS_EMOTION,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    TTS_LANGUAGES,
    TTS_VOICES,
)
from .entity import YandexAIBaseLLMEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TTS entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "tts":
            continue
        async_add_entities(
            [YandexTTSEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class YandexTTSEntity(TextToSpeechEntity, YandexAIBaseLLMEntity):
    """Yandex AI Studio text-to-speech entity."""

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the TTS entity."""
        super().__init__(entry, subentry, DEFAULT_TTS_VOICE)

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return "ru-RU"

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return TTS_LANGUAGES

    @property
    def supported_options(self) -> list[str]:
        """Return list of supported options like voice, emotion, speed."""
        return [ATTR_VOICE, "emotion", "speed"]

    @property
    def default_options(self) -> Mapping[str, Any]:
        """Return a mapping with the default options."""
        options = self.subentry.data
        return {
            ATTR_VOICE: options.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE),
            "emotion": options.get(CONF_TTS_EMOTION, DEFAULT_TTS_EMOTION),
            "speed": str(options.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED)),
        }

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return a list of supported voices for a language."""
        if not (voices := TTS_VOICES.get(language)):
            return None
        return [Voice(voice_id, voice_name) for voice_id, voice_name in voices]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Load TTS audio from Yandex SpeechKit."""
        headers = {"Authorization": f"Api-Key {self.api_key}"}

        entry_options = self.subentry.data
        voice = str(
            options.get(
                ATTR_VOICE, entry_options.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE)
            )
        )
        emotion = str(
            options.get(
                "emotion", entry_options.get(CONF_TTS_EMOTION, DEFAULT_TTS_EMOTION)
            )
        )
        if ":" in voice:
            voice, emotion = voice.split(":", 1)

        speed = str(
            options.get("speed", entry_options.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED))
        )

        data: dict[str, str] = {
            "text": message,
            "lang": language,
            "voice": voice,
            "speed": speed,
            "folderId": self.folder_id,
        }
        if emotion and language == "ru-RU":
            data["emotion"] = emotion

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp,
            ):
                if resp.status == 200:
                    audio = await resp.read()
                    return ("ogg", audio)
                text = await resp.text()
                _LOGGER.error("Yandex TTS failed: %s %s", resp.status, text)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Yandex TTS exception: %s", err)

        return (None, None)

