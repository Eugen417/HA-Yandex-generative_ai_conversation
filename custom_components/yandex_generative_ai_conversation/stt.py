"""Speech to text support for Yandex AI Studio."""

from collections.abc import AsyncIterable
import logging

import aiohttp

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_STT_LANGUAGE,
    CONF_STT_MODEL,
    DEFAULT_STT_LANGUAGE,
    DEFAULT_STT_MODEL,
    DOMAIN,
    STT_LANGUAGES,
)
from .entity import YandexAIBaseLLMEntity

_LOGGER = logging.getLogger(__name__)

_SHORT_LANG_MAP = {
    "ru": "ru-RU",
    "en": "en-US",
    "kk": "kk-KZ",
    "tr": "tr-TR",
    "de": "de-DE",
    "es": "es-ES",
    "fi": "fi-FI",
    "fr": "fr-FR",
    "he": "he-HE",
    "it": "it-IT",
    "nl": "nl-NL",
    "pl": "pl-PL",
    "pt": "pt-PT",
    "sv": "sv-SE",
    "uz": "uz-UZ",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up STT entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "stt":
            continue
        async_add_entities(
            [YandexSTTEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class YandexSTTEntity(SpeechToTextEntity, YandexAIBaseLLMEntity):
    """Yandex AI Studio speech-to-text entity."""

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the STT entity."""
        super().__init__(entry, subentry, DEFAULT_STT_MODEL)

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return STT_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported samplerates."""
        return [
            AudioSampleRates.SAMPLERATE_8000,
            AudioSampleRates.SAMPLERATE_16000,
            AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to Yandex STT service."""
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk

        if not audio_data:
            return SpeechResult("", SpeechResultState.ERROR)

        headers = {"Authorization": f"Api-Key {self.api_key}"}

        is_ogg = (
            metadata.format == AudioFormats.OGG
            or metadata.codec == AudioCodecs.OPUS
            or str(metadata.format) == "ogg"
        )
        format_param = "oggopus" if is_ogg else "lpcm"

        raw_rate = metadata.sample_rate
        sample_rate = int(raw_rate.value if hasattr(raw_rate, "value") else raw_rate)

        lang = metadata.language or self.subentry.data.get(
            CONF_STT_LANGUAGE, DEFAULT_STT_LANGUAGE
        )
        lang = _SHORT_LANG_MAP.get(lang, lang)
        topic = self.subentry.data.get(CONF_STT_MODEL, DEFAULT_STT_MODEL)

        params: dict[str, str | int] = {
            "folderId": self.folder_id,
            "lang": lang,
            "topic": topic,
            "format": format_param,
        }
        if format_param == "lpcm":
            params["sampleRateHertz"] = sample_rate

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
                    headers=headers,
                    params=params,
                    data=audio_data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp,
            ):
                if resp.status == 200:
                    res = await resp.json()
                    text = res.get("result", "")
                    if text:
                        if self.hass is not None:
                            async_dispatcher_send(
                                self.hass,
                                f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                                {
                                    "requests": 1,
                                    "cost_rub": 0.15,
                                    "model": topic,
                                },
                            )
                        return SpeechResult(text, SpeechResultState.SUCCESS)
                    _LOGGER.warning("Yandex STT returned empty result: %s", res)
                    return SpeechResult("", SpeechResultState.ERROR)

                err_text = await resp.text()
                _LOGGER.error("Yandex STT failed: %s %s", resp.status, err_text)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Yandex STT exception: %s", err)

        return SpeechResult("", SpeechResultState.ERROR)

