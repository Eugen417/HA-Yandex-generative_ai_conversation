"""Text to speech support for Yandex AI Studio."""

import asyncio
import base64
from collections.abc import AsyncGenerator, Mapping
import contextlib
import json
import logging
import re
import struct
from typing import Any

import aiohttp

try:
    from sentence_stream import SentenceBoundaryDetector
except ImportError:
    SentenceBoundaryDetector = None  # type: ignore[assignment,misc]

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TTSAudioRequest,
    TTSAudioResponse,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_TTS_EMOTION,
    CONF_TTS_PITCH_SHIFT,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_TTS_EMOTION,
    DEFAULT_TTS_PITCH_SHIFT,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    DOMAIN,
    TTS_GENERAL_COST_PER_1K_CHARS,
    TTS_LANGUAGES,
    TTS_LIVETTS_COST_PER_1K_CHARS,
    TTS_VOICES,
)
from .entity import YandexAIBaseLLMEntity
from .helpers import build_yandex_headers

_LOGGER = logging.getLogger(__name__)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…\n])\s+")
_MARKDOWN_CLEAN_RE = re.compile(r"[*_`~]+")


class _FallbackSentenceDetector:
    """Lightweight sentence splitter used if sentence_stream is unavailable."""

    def __init__(self) -> None:
        self._buf = ""

    def add_chunk(self, chunk: str) -> list[str]:
        self._buf += chunk
        parts = _SENTENCE_SPLIT_RE.split(self._buf)
        if len(parts) <= 1:
            return []
        self._buf = parts[-1]
        return [p for p in parts[:-1] if p.strip()]

    def finish(self) -> str:
        rem = self._buf.strip()
        self._buf = ""
        return rem


def _build_streaming_wav_header(sample_rate: int) -> bytes:
    """Build a 44-byte RIFF WAV header for a 16-bit mono PCM stream."""
    byte_rate = sample_rate * 2
    max_len = 0x7FFFFFFF
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        max_len,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        byte_rate,
        2,
        16,
        b"data",
        max_len,
    )


def _clean_tts_sentence(text: str) -> str:
    """Strip markdown emphasis tokens so TTS does not read formatting aloud."""
    return _MARKDOWN_CLEAN_RE.sub("", text).strip()

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
    "dasha": {"neutral", "good", "friendly", "whisper"},
    "julia": {"neutral", "strict"},
    "lera": {"neutral", "friendly"},
    "masha": {"good", "strict", "friendly"},
    "marina": {"neutral", "whisper", "friendly"},
    "alexander": {"neutral", "good"},
    "kirill": {"neutral", "strict", "good"},
    "anton": {"neutral", "good"},
    "madi_ru": set(),
    "saule_ru": {"neutral", "strict", "whisper"},
    "zamira_ru": {"neutral", "strict", "friendly"},
    "zhanar_ru": {"neutral", "strict", "friendly"},
    "yulduz_ru": {"neutral", "strict", "friendly", "whisper"},
    "saule": {"neutral", "strict", "whisper"},
    "zhanar": {"neutral", "friendly"},
    "zamira": {"neutral", "strict", "friendly"},
    "lola": set(),
    "yulduz": {"neutral", "strict", "friendly", "whisper"},
    "naomi": {"modern", "classic"},
}

LIVETTS_VOICE_ROLES: dict[str, set[str]] = {
    "irina": {"neutral", "formal", "support", "narrator", "sales"},
    "sofia": {"support", "casual"},
    "vera": {"support", "casual"},
    "denis": {"neutral", "casual", "formal", "sales"},
    "vasily": {"support", "sales"},
    "sergey": {"support", "sales"},
}

LIVETTS_DEFAULT_ROLE: dict[str, str] = {
    "irina": "neutral",
    "sofia": "support",
    "vera": "support",
    "denis": "neutral",
    "vasily": "support",
    "sergey": "support",
}


def _build_v3_synthesis_payload(
    *,
    text: str,
    voice: str,
    emotion: str,
    speed: str,
    pitch_shift: float,
    output_audio_spec: dict[str, Any],
) -> dict[str, Any]:
    """Build SpeechKit v3 utteranceSynthesis payload for both general v3 and livetts voices."""
    if voice in LIVETTS_VOICE_ROLES:
        allowed_live = LIVETTS_VOICE_ROLES[voice]
        role = emotion
        if role in ("good", "friendly") and "casual" in allowed_live:
            role = "casual"
        elif role == "strict" and "formal" in allowed_live:
            role = "formal"
        if role not in allowed_live:
            role = LIVETTS_DEFAULT_ROLE[voice]
        # Note: per Yandex tts.proto, speed and pitch_shift are NOT supported by `livetts`
        return {
            "model": "livetts",
            "text": text,
            "hints": [
                {"voice": voice},
                {"role": role},
            ],
            "outputAudioSpec": output_audio_spec,
            "loudnessNormalizationType": "LUFS",
            "unsafeMode": True,
        }

    hints: list[dict[str, Any]] = [
        {"voice": voice},
        {"speed": float(speed)},
    ]
    if pitch_shift:
        hints.append({"pitchShift": max(-1000.0, min(1000.0, pitch_shift))})

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
    elif "modern" in allowed_roles:
        hints.append({"role": "modern"})

    return {
        "text": text,
        "hints": hints,
        "outputAudioSpec": output_audio_spec,
        "loudnessNormalizationType": "LUFS",
        "unsafeMode": True,
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
        """Return list of supported options like voice, emotion, speed, pitch_shift."""
        return [ATTR_VOICE, "emotion", "speed", "pitch_shift"]

    @property
    def default_options(self) -> Mapping[str, Any]:
        """Return a mapping with the default options."""
        options = self.subentry.data
        return {
            ATTR_VOICE: options.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE),
            "emotion": options.get(CONF_TTS_EMOTION, DEFAULT_TTS_EMOTION),
            "speed": str(options.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED)),
            "pitch_shift": int(
                options.get(CONF_TTS_PITCH_SHIFT, DEFAULT_TTS_PITCH_SHIFT)
            ),
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
        raw_pitch = options.get(
            "pitch_shift",
            entry_options.get(CONF_TTS_PITCH_SHIFT, DEFAULT_TTS_PITCH_SHIFT),
        )
        try:
            pitch_shift = float(raw_pitch)
        except (TypeError, ValueError):
            pitch_shift = 0.0

        # Voices that require SpeechKit API v3 (general v3 & 4th-gen LiveTTS)
        if voice in V3_VOICE_ROLES or voice in LIVETTS_VOICE_ROLES:
            return await self._async_synthesize_v3(
                message, voice, emotion, speed, pitch_shift
            )

        headers = build_yandex_headers(
            self.api_key,
            self.folder_id,
            disable_data_logging=self.disable_data_logging,
            include_content_type=False,
        )
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
            session = async_get_clientsession(self.hass)
            async with session.post(
                "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
                headers=headers,
                data=data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
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
        self,
        message: str,
        voice: str,
        emotion: str,
        speed: str,
        pitch_shift: float = 0.0,
    ) -> TtsAudioType:
        """Synthesize speech using Yandex SpeechKit REST API v3 for 3rd-gen voices."""
        headers = build_yandex_headers(
            self.api_key,
            self.folder_id,
            disable_data_logging=self.disable_data_logging,
        )
        payload = _build_v3_synthesis_payload(
            text=message,
            voice=voice,
            emotion=emotion,
            speed=speed,
            pitch_shift=pitch_shift,
            output_audio_spec={
                "containerAudio": {
                    "containerAudioType": "MP3",
                }
            },
        )

        try:
            session = async_get_clientsession(self.hass)
            async with session.post(
                "https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
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
                        rate = (
                            TTS_LIVETTS_COST_PER_1K_CHARS
                            if voice in LIVETTS_VOICE_ROLES
                            else TTS_GENERAL_COST_PER_1K_CHARS
                        )
                        async_dispatcher_send(
                            self.hass,
                            f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                            {
                                "chars": chars,
                                "cost_rub": chars * rate / 1000.0,
                                "model": voice,
                            },
                        )
                    return ("mp3", b"".join(audio_chunks))
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Yandex TTS v3 exception: %s", err)

        return (None, None)

    def _resolve_voice_options(
        self, options: Mapping[str, Any]
    ) -> tuple[str, str, str, float]:
        """Extract normalized voice, emotion, speed, and pitch_shift."""
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
        raw_pitch = options.get(
            "pitch_shift",
            entry_options.get(CONF_TTS_PITCH_SHIFT, DEFAULT_TTS_PITCH_SHIFT),
        )
        try:
            pitch_shift = float(raw_pitch)
        except (TypeError, ValueError):
            pitch_shift = 0.0
        return voice, emotion, speed, pitch_shift

    async def _async_stream_pcm_v1(
        self,
        sentence: str,
        language: str,
        voice: str,
        emotion: str,
        speed: str,
    ) -> AsyncGenerator[bytes]:
        """Yield 48kHz 16-bit mono PCM chunks for classic v1 SpeechKit voices."""
        headers = build_yandex_headers(
            self.api_key,
            self.folder_id,
            disable_data_logging=self.disable_data_logging,
            include_content_type=False,
        )
        data: dict[str, str] = {
            "text": sentence,
            "lang": language,
            "voice": voice,
            "speed": speed,
            "format": "lpcm",
            "sampleRateHertz": "48000",
            "folderId": self.folder_id,
        }
        allowed_emotions = V1_VOICE_EMOTIONS.get(voice)
        if allowed_emotions:
            if emotion in allowed_emotions:
                data["emotion"] = emotion
            elif "neutral" in allowed_emotions:
                data["emotion"] = "neutral"

        session = async_get_clientsession(self.hass)
        async with session.post(
            "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
            headers=headers,
            data=data,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                raise HomeAssistantError(
                    f"Yandex TTS v1 stream failed ({resp.status}): {err_text}"
                )
            carry = b""
            async for chunk in resp.content.iter_chunked(4096):
                buf = carry + chunk
                if len(buf) & 1:
                    carry = buf[-1:]
                    buf = buf[:-1]
                else:
                    carry = b""
                if buf:
                    yield buf

    async def _async_stream_pcm_v3(
        self,
        sentence: str,
        voice: str,
        emotion: str,
        speed: str,
        pitch_shift: float,
    ) -> AsyncGenerator[bytes]:
        """Yield 22050Hz 16-bit mono PCM chunks incrementally from SpeechKit v3."""
        headers = build_yandex_headers(
            self.api_key,
            self.folder_id,
            disable_data_logging=self.disable_data_logging,
        )
        payload = _build_v3_synthesis_payload(
            text=sentence,
            voice=voice,
            emotion=emotion,
            speed=speed,
            pitch_shift=pitch_shift,
            output_audio_spec={
                "rawAudio": {
                    "audioEncoding": "LINEAR16_PCM",
                    "sampleRateHertz": 22050,
                }
            },
        )

        session = async_get_clientsession(self.hass)
        async with session.post(
            "https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                raise HomeAssistantError(
                    f"Yandex TTS v3 stream failed ({resp.status}): {err_text}"
                )
            byte_buf = b""
            carry = b""
            async for raw_bytes in resp.content.iter_any():
                byte_buf += raw_bytes
                while b"\n" in byte_buf:
                    raw_line, byte_buf = byte_buf.split(b"\n", 1)
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    chunk_obj = json.loads(line)
                    result_obj = chunk_obj.get("result", chunk_obj)
                    b64_data = result_obj.get("audioChunk", {}).get("data")
                    if b64_data:
                        pcm = carry + base64.b64decode(b64_data)
                        if len(pcm) & 1:
                            carry = pcm[-1:]
                            pcm = pcm[:-1]
                        else:
                            carry = b""
                        if pcm:
                            yield pcm
            if rem := byte_buf.decode("utf-8", errors="replace").strip():
                with contextlib.suppress(json.JSONDecodeError):
                    chunk_obj = json.loads(rem)
                    result_obj = chunk_obj.get("result", chunk_obj)
                    if b64_data := result_obj.get("audioChunk", {}).get("data"):
                        pcm = carry + base64.b64decode(b64_data)
                        if len(pcm) >= 2:
                            yield pcm[: len(pcm) & ~1]

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse:
        """Stream synthesized speech sentence-by-sentence as a seamless WAV PCM stream."""
        return TTSAudioResponse("wav", self._process_tts_stream(request))

    async def _process_tts_stream(
        self, request: TTSAudioRequest
    ) -> AsyncGenerator[bytes]:
        """Consume incoming LLM text chunks and yield continuous WAV audio bytes."""
        voice, emotion, speed, pitch_shift = self._resolve_voice_options(
            request.options
        )
        is_v3_voice = voice in V3_VOICE_ROLES or voice in LIVETTS_VOICE_ROLES
        sample_rate = 22050 if is_v3_voice else 48000

        detector = (
            SentenceBoundaryDetector()
            if SentenceBoundaryDetector is not None
            else _FallbackSentenceDetector()
        )
        sentences: list[str] = []
        sentences_ready = asyncio.Event()
        sentences_complete = False

        async def _collect_sentences() -> None:
            nonlocal sentences_complete
            try:
                async for text_chunk in request.message_gen:
                    if not text_chunk:
                        continue
                    for sentence in detector.add_chunk(text_chunk):
                        if cleaned := _clean_tts_sentence(sentence):
                            sentences.append(cleaned)
                    if sentences:
                        sentences_ready.set()
                if tail := _clean_tts_sentence(detector.finish()):
                    sentences.append(tail)
            finally:
                sentences_complete = True
                sentences_ready.set()

        collector_task = self.hass.async_create_background_task(
            _collect_sentences(), f"{DOMAIN}_tts_stream_{self.subentry.subentry_id}"
        )

        header_sent = False
        total_chars = 0
        sentence_schedule = [1, 3]

        try:
            while True:
                await sentences_ready.wait()
                if not sentences_complete:
                    sentences_ready.clear()

                if not sentences:
                    if sentences_complete:
                        break
                    continue

                batch_queue = sentences[:]
                sentences.clear()

                while batch_queue:
                    if sentence_schedule:
                        take = sentence_schedule.pop(0)
                        current_batch = batch_queue[:take]
                        batch_queue = batch_queue[len(current_batch) :]
                    else:
                        current_batch = batch_queue[:]
                        batch_queue.clear()

                    utterance = " ".join(current_batch).strip()
                    if not utterance:
                        continue

                    if not header_sent:
                        header_sent = True
                        yield _build_streaming_wav_header(sample_rate)

                    total_chars += len(utterance)
                    if is_v3_voice:
                        async for pcm_chunk in self._async_stream_pcm_v3(
                            utterance, voice, emotion, speed, pitch_shift
                        ):
                            yield pcm_chunk
                    else:
                        async for pcm_chunk in self._async_stream_pcm_v1(
                            utterance, request.language, voice, emotion, speed
                        ):
                            yield pcm_chunk

            if not header_sent:
                yield _build_streaming_wav_header(sample_rate) + (b"\x00" * 320)

            if total_chars > 0 and self.hass is not None:
                rate = (
                    TTS_LIVETTS_COST_PER_1K_CHARS
                    if voice in LIVETTS_VOICE_ROLES
                    else TTS_GENERAL_COST_PER_1K_CHARS
                )
                async_dispatcher_send(
                    self.hass,
                    f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                    {
                        "chars": total_chars,
                        "cost_rub": total_chars * rate / 1000.0,
                        "model": voice,
                    },
                )
        finally:
            if not collector_task.done():
                collector_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await collector_task


