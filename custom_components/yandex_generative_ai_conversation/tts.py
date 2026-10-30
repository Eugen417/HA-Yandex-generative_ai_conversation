"""Text to speech support for Yandex AI Studio."""

from collections.abc import Mapping
import base64
import json
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
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_TTS_EMOTION,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_TTS_EMOTION,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    DOMAIN,
    TTS_LANGUAGES,
    TTS_VOICES,
)
from .entity import YandexAIBaseLLMEntity

_LOGGER = logging.getLogger(__name__)

V1_VOICE_EMOTIONS: dict[str, set[str]] = {
    "alena": {"neutral", "good"},
    "filipp": {"neutral"},
    "ermil": {"neutral", "good"},
    "jane": {"neutral", "good", "evil"},
    "madirus": {"neutral"},
    "omazh": {"neutral", "evil"},
    "zahar": {"neutral", "good"},
}

V3_VOICE_ROLES: dict[str, set[str]] = {
    "dasha": {"neutral", "friendly", "whisper"},
    "julia": {"neutral", "strict"},
    "lera": {"neutral", "friendly"},
    "masha": {"good", "strict", "friendly"},
    "marina": {"neutral", "whisper", "friendly"},
    "alexander": {"neutral", "good"},
    "kirill": {"neutral", "strict", "good"},
    "anton": {"neutral", "good"},
    "saule": {"neutral", "strict", "whisper"},
    "zhanar": {"neutral", "friendly"},
    "lola": set(),
    "yulduz": {"neutral", "strict", "friendly", "whisper"},
}


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
        """Load TTS audio from Yandex SpeechKit (API v1 & API v3)."""
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

        # Voices that only exist in SpeechKit API v3
        if voice in V3_VOICE_ROLES:
            return await self._async_synthesize_v3(message, voice, emotion, speed)

        headers = {"Authorization": f"Api-Key {self.api_key}"}
        data: dict[str, str] = {
            "text": message,
            "lang": language,
            "voice": voice,
            "speed": speed,
            "folderId": self.folder_id,
        }
        allowed_emotions = V1_VOICE_EMOTIONS.get(voice)
        if allowed_emotions:
            if emotion in allowed_emotions:
                data["emotion"] = emotion
            elif "neutral" in allowed_emotions:
                data["emotion"] = "neutral"

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
                    if self.hass is not None:
                        chars = len(message)
                        async_dispatcher_send(
                            self.hass,
                            f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                            {
                                "chars": chars,
                                "cost_rub": chars * 1.32 / 1000.0,
                                "model": voice,
                            },
                        )
                    return ("ogg", audio)
                text = await resp.text()
                _LOGGER.error("Yandex TTS v1 failed (%s): %s %s", voice, resp.status, text)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Yandex TTS v1 exception: %s", err)

        return (None, None)

    async def _async_synthesize_v3(
        self, message: str, voice: str, emotion: str, speed: str
    ) -> TtsAudioType:
        """Synthesize speech using Yandex SpeechKit REST API v3 for 3rd-gen voices."""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self.folder_id,
        }
        hints: list[dict[str, Any]] = [
            {"voice": voice},
            {"speed": float(speed)},
        ]
        allowed_roles = V3_VOICE_ROLES.get(voice, set())
        role = emotion
        if role == "good" and "good" not in allowed_roles and "friendly" in allowed_roles:
            role = "friendly"
        elif role == "evil" and "evil" not in allowed_roles and "strict" in allowed_roles:
            role = "strict"

        if role in allowed_roles:
            hints.append({"role": role})
        elif "neutral" in allowed_roles:
            hints.append({"role": "neutral"})

        payload = {
            "text": message,
            "hints": hints,
            "outputAudioSpec": {
                "containerAudio": {
                    "containerAudioType": "MP3",
                }
            },
            "loudnessNormalizationType": "LUFS",
            "unsafeMode": True,
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp,
            ):
                text = await resp.text()
                if resp.status != 200:
                    _LOGGER.error(
                        "Yandex TTS v3 failed (%s): %s %s", voice, resp.status, text
                    )
                    return (None, None)

                audio_chunks: list[bytes] = []
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    chunk_obj = json.loads(line)
                    result_obj = chunk_obj.get("result", chunk_obj)
                    b64_data = result_obj.get("audioChunk", {}).get("data")
                    if b64_data:
                        audio_chunks.append(base64.b64decode(b64_data))

                if audio_chunks:
                    if self.hass is not None:
                        chars = len(message)
                        async_dispatcher_send(
                            self.hass,
                            f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                            {
                                "chars": chars,
                                "cost_rub": chars * 1.32 / 1000.0,
                                "model": voice,
                            },
                        )
                    return ("mp3", b"".join(audio_chunks))
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Yandex TTS v3 exception: %s", err)

        return (None, None)

