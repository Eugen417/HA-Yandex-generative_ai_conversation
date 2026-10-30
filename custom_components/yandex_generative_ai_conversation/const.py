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
DEFAULT_AI_TASK_IMAGE_NAME = "Yandex AI Task image"

DEFAULT_PROMPT = (
    "Ты голосовой помощник для Home Assistant.\n"
    "Отвечай правдиво на вопросы об окружающем мире.\n"
    "Отвечай просто, кратко и по делу обычным текстом на русском языке."
)
DEFAULT_CHAT_MODEL = "yandexgpt/latest"
DEFAULT_IMAGE_MODEL = "aliceai-image-art-3.0"
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
    "aliceai-llm/latest",
    "qwen3-235b-a22b-fp8/latest",
    "yandexgpt/rc",
    "yandexgpt-lite/rc",
]

CHAT_MODEL_LABELS: dict[str, str] = {
    "yandexgpt/latest": "YandexGPT Pro (1.20 ₽ / 1K — рекомендуется для управления УД)",
    "yandexgpt-lite/latest": "YandexGPT Lite (0.20 ₽ / 1K — для текста и AI Task, без сложного управления)",
    "aliceai-llm/latest": "Alice AI LLM (0.50 ₽ / 1K — диалоговая)",
    "qwen3-235b-a22b-fp8/latest": "Qwen3 235B (0.50 ₽ / 1K)",
    "yandexgpt/rc": "YandexGPT Pro RC (1.20 ₽ / 1K)",
    "yandexgpt-lite/rc": "YandexGPT Lite RC (0.20 ₽ / 1K)",
}

IMAGE_MODELS = [
    "aliceai-image-art-3.0",
]

IMAGE_MODEL_LABELS: dict[str, str] = {
    "aliceai-image-art-3.0": "Alice AI ART 3.0 (2.23 ₽ / изображение)",
}

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
        ("dasha", "Даша (Нейтральный)"),
        ("dasha:friendly", "Даша (Дружелюбный)"),
        ("dasha:whisper", "Даша (Шёпот)"),
        ("julia", "Юлия (Нейтральный)"),
        ("julia:strict", "Юлия (Строгий)"),
        ("lera", "Лера (Нейтральный)"),
        ("lera:friendly", "Лера (Дружелюбный)"),
        ("masha", "Маша (Дружелюбный)"),
        ("masha:good", "Маша (Радостный)"),
        ("masha:strict", "Маша (Строгий)"),
        ("marina", "Марина (Нейтральный)"),
        ("marina:friendly", "Марина (Дружелюбный)"),
        ("marina:whisper", "Марина (Шёпот)"),
        ("alexander", "Александр (Нейтральный)"),
        ("alexander:good", "Александр (Радостный)"),
        ("kirill", "Кирилл (Нейтральный)"),
        ("kirill:good", "Кирилл (Радостный)"),
        ("kirill:strict", "Кирилл (Строгий)"),
        ("anton", "Антон (Нейтральный)"),
        ("anton:good", "Антон (Радостный)"),
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
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
}

RECOMMENDED_AI_TASK_IMAGE_OPTIONS: dict[str, Any] = {
    CONF_RECOMMENDED: True,
    CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
}

PLATFORMS = [
    Platform.CONVERSATION,
    Platform.STT,
    Platform.TTS,
    Platform.AI_TASK,
    Platform.SENSOR,
]

