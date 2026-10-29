"""Constants for the Yandex AI Studio integration."""

from typing import Any

from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT, Platform
from homeassistant.helpers import llm

DOMAIN = "yandex_generative_ai_conversation"
CONF_FOLDER_ID = "folder_id"
CONF_API_KEY = "api_key"

CONF_RECOMMENDED = "recommended"
CONF_CHAT_MODEL = "chat_model"
CONF_IMAGE_MODEL = "image_model"
CONF_TEMPERATURE = "temperature"
CONF_MAX_TOKENS = "max_tokens"

CONF_TTS_VOICE = "tts_voice"
CONF_TTS_EMOTION = "tts_emotion"
CONF_TTS_SPEED = "tts_speed"

CONF_STT_MODEL = "stt_model"
CONF_STT_LANGUAGE = "stt_language"

DEFAULT_TITLE = "Yandex AI Studio"
DEFAULT_CONVERSATION_NAME = "Yandex AI Conversation"
DEFAULT_STT_NAME = "Yandex AI STT"
DEFAULT_TTS_NAME = "Yandex AI TTS"
DEFAULT_AI_TASK_NAME = "Yandex AI Task"
DEFAULT_AI_TASK_IMAGE_NAME = "Yandex AI Task image"

DEFAULT_PROMPT = (
    "Ты полезный голосовой помощник для умного дома Home Assistant. "
    "Отвечай кратко, точно и по делу на русском языке."
)
DEFAULT_CHAT_MODEL = "yandexgpt/latest"
DEFAULT_IMAGE_MODEL = "yandex-art/latest"
DEFAULT_STT_MODEL = "general"
DEFAULT_STT_LANGUAGE = "ru-RU"

RECOMMENDED_TEMPERATURE = 0.3
RECOMMENDED_MAX_TOKENS = 2000

DEFAULT_TTS_VOICE = "alena"
DEFAULT_TTS_EMOTION = "good"
DEFAULT_TTS_SPEED = 1.0

CHAT_MODELS = [
    "yandexgpt/latest",
    "yandexgpt-lite/latest",
    "yandexgpt/rc",
    "yandexgpt-lite/rc",
    "aliceai-llm/latest",
    "qwen3-235b-a22b-fp8/latest",
]

IMAGE_MODELS = [
    "yandex-art/latest",
]

STT_MODELS = [
    "general",
    "general:rc",
    "general:deprecated",
]

STT_LANGUAGES = [
    "ru-RU",
    "en-US",
    "kk-KZ",
    "tr-TR",
    "de-DE",
    "es-ES",
    "fi-FI",
    "fr-FR",
    "he-HE",
    "it-IT",
    "nl-NL",
    "pl-PL",
    "pt-PT",
    "pt-BR",
    "sv-SE",
    "uz-UZ",
    "auto",
]

TTS_VOICES: dict[str, list[tuple[str, str]]] = {
    "ru-RU": [
        ("alena", "Алёна"),
        ("alena:good", "Алёна (Радостный)"),
        ("alena:neutral", "Алёна (Нейтральный)"),
        ("filipp", "Филипп"),
        ("ermil", "Эрмил"),
        ("ermil:good", "Эрмил (Радостный)"),
        ("ermil:neutral", "Эрмил (Нейтральный)"),
        ("jane", "Джейн"),
        ("jane:good", "Джейн (Радостный)"),
        ("jane:evil", "Джейн (Раздраженный)"),
        ("jane:neutral", "Джейн (Нейтральный)"),
        ("madirus", "Мадирус"),
        ("omazh", "Омаж"),
        ("omazh:evil", "Омаж (Раздраженный)"),
        ("omazh:neutral", "Омаж (Нейтральный)"),
        ("zahar", "Захар"),
        ("zahar:good", "Захар (Радостный)"),
        ("zahar:neutral", "Захар (Нейтральный)"),
        ("dasha", "Даша"),
        ("julia", "Юлия"),
        ("lera", "Лера"),
        ("masha", "Маша"),
        ("marina", "Марина"),
        ("alexander", "Александр"),
        ("kirill", "Кирилл"),
        ("anton", "Антон"),
    ],
    "en-US": [
        ("john", "John"),
    ],
    "de-DE": [
        ("lea", "Lea"),
    ],
    "kk-KK": [
        ("amira", "Amira"),
        ("madi", "Madi"),
        ("saule", "Saule"),
        ("zhanar", "Zhanar"),
    ],
    "uz-UZ": [
        ("nigora", "Nigora"),
        ("lola", "Lola"),
        ("yulduz", "Yulduz"),
    ],
    "he-IL": [
        ("naomi", "Naomi"),
    ],
}

TTS_LANGUAGES = list(TTS_VOICES.keys())

RECOMMENDED_CONVERSATION_OPTIONS: dict[str, Any] = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: DEFAULT_PROMPT,
    CONF_CHAT_MODEL: DEFAULT_CHAT_MODEL,
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
}

RECOMMENDED_STT_OPTIONS: dict[str, Any] = {
    CONF_STT_MODEL: DEFAULT_STT_MODEL,
    CONF_STT_LANGUAGE: DEFAULT_STT_LANGUAGE,
}

RECOMMENDED_TTS_OPTIONS: dict[str, Any] = {
    CONF_TTS_VOICE: DEFAULT_TTS_VOICE,
    CONF_TTS_EMOTION: DEFAULT_TTS_EMOTION,
    CONF_TTS_SPEED: DEFAULT_TTS_SPEED,
}

RECOMMENDED_AI_TASK_OPTIONS: dict[str, Any] = {
    CONF_RECOMMENDED: True,
    CONF_CHAT_MODEL: DEFAULT_CHAT_MODEL,
    CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
}

PLATFORMS = [
    Platform.CONVERSATION,
    Platform.STT,
    Platform.TTS,
    Platform.AI_TASK,
]

