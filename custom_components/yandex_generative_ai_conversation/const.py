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
CONF_WEB_SEARCH = "web_search"
CONF_STREAMING = "streaming"
CONF_REASONING_EFFORT = "reasoning_effort"
CONF_DISABLE_DATA_LOGGING = "disable_data_logging"

CONF_TTS_VOICE = "tts_voice"
CONF_TTS_EMOTION = "tts_emotion"
CONF_TTS_SPEED = "tts_speed"
CONF_TTS_PITCH_SHIFT = "tts_pitch_shift"

CONF_STT_MODEL = "stt_model"
CONF_STT_LANGUAGE = "stt_language"

DEFAULT_TITLE = "Yandex AI Studio"
DEFAULT_CONVERSATION_NAME = "Yandex AI Conversation"
DEFAULT_STT_NAME = "Yandex AI STT"
DEFAULT_TTS_NAME = "Yandex AI TTS"
DEFAULT_AI_TASK_NAME = "Yandex AI Task"
DEFAULT_AI_TASK_IMAGE_NAME = "Yandex AI Task image"

DEFAULT_PROMPT = (
    "Ты голосовой помощник для Home Assistant.\n"
    "Отвечай правдиво на вопросы об окружающем мире.\n"
    "Отвечай просто, кратко и по делу обычным текстом на русском языке."
)
DEFAULT_CHAT_MODEL = "yandexgpt-5.1"
DEFAULT_IMAGE_MODEL = "aliceai-image-art-3.0"
DEFAULT_STT_MODEL = "general"
DEFAULT_STT_LANGUAGE = "ru-RU"

RECOMMENDED_TEMPERATURE = 0.3
RECOMMENDED_MAX_TOKENS = 2000

DEFAULT_TTS_VOICE = "alena"
DEFAULT_TTS_EMOTION = "good"
DEFAULT_TTS_SPEED = 1.0
DEFAULT_TTS_PITCH_SHIFT = 0

DEFAULT_DISABLE_DATA_LOGGING = True
DEFAULT_WEB_SEARCH = False
DEFAULT_STREAMING = True
DEFAULT_REASONING_EFFORT = "none"

REASONING_EFFORT_OPTIONS = [
    "none",
    "low",
    "medium",
    "high",
]

DEFAULT_VISION_MODEL = "qwen3.6-35b-a3b"

CHAT_MODELS = [
    "yandexgpt-5.1",
    "aliceai-llm-flash",
    "aliceai-llm",
    "deepseek-v4.1-flash",
    "qwen3.6-35b-a3b",
    "yandexgpt-5-pro",
    "yandexgpt/latest",
    "yandexgpt-lite/latest",
    "gemma-3-27b-it/latest",
    "qwen3-235b-a22b-fp8/latest",
]

CHAT_MODEL_LABELS: dict[str, str] = {
    "yandexgpt-5.1": "YandexGPT Pro 5.1 (0.80 / 0.80 ₽ за 1K — 32k, флагман для УД)",
    "aliceai-llm-flash": "Alice AI LLM Flash (0.10 / 0.20 ₽ за 1K — 64k, сверхбыстрая для голоса и чатов)",
    "aliceai-llm": "Alice AI LLM (0.50 / 1.20 ₽ за 1K — 128k, живой диалог)",
    "deepseek-v4.1-flash": "DeepSeek V4.1 Flash (0.30 / 0.50 ₽ за 1K — 1M контекст, ИИ-агенты и MCP)",
    "qwen3.6-35b-a3b": "Qwen3.6 35B Vision (0.20 / 0.30 ₽ за 1K — 256k, анализ камер и мультимодальность)",
    "yandexgpt-5-pro": "YandexGPT Pro 5 (1.20 / 1.20 ₽ за 1K — 32k)",
    "yandexgpt/latest": "YandexGPT Pro [legacy alias] (1.20 ₽ / 1K)",
    "yandexgpt-lite/latest": "YandexGPT Lite [legacy] (0.20 ₽ / 1K)",
    "gemma-3-27b-it/latest": "Gemma 3 27B Vision [legacy] (0.40 ₽ / 1K)",
    "qwen3-235b-a22b-fp8/latest": "Qwen3 235B [legacy] (0.50 ₽ / 1K)",
}

# Exact synchronous rates (input_rub_per_1k, output_rub_per_1k) incl. VAT
MODEL_TOKEN_RATES_PER_1K: list[tuple[str, float, float]] = [
    ("aliceai-llm-flash", 0.10, 0.20),
    ("qwen3.6", 0.20, 0.30),
    ("deepseek-v4.1", 0.30, 0.50),
    ("deepseek", 0.30, 0.50),
    ("lite", 0.20, 0.20),
    ("gemma", 0.40, 0.40),
    ("qwen3-235b", 0.50, 0.50),
    ("aliceai-llm", 0.50, 1.20),
    ("yandexgpt-5.1", 0.80, 0.80),
    ("yandexgpt/rc", 0.80, 0.80),
    ("yandexgpt", 1.20, 1.20),
]

WEB_SEARCH_COST_RUB = 0.915
TTS_GENERAL_COST_PER_1K_CHARS = 1.32
TTS_LIVETTS_COST_PER_1K_CHARS = 3.25

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
    "he-IL",
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
        ("irina", "Ирина LiveTTS (Нейтральный)"),
        ("irina:narrator", "Ирина LiveTTS (Рассказчик)"),
        ("irina:formal", "Ирина LiveTTS (Формальный)"),
        ("irina:support", "Ирина LiveTTS (Поддержка)"),
        ("irina:sales", "Ирина LiveTTS (Продажи)"),
        ("sofia:casual", "Софья LiveTTS (Разговорный)"),
        ("sofia", "Софья LiveTTS (Поддержка)"),
        ("vera:casual", "Вера LiveTTS (Разговорный)"),
        ("vera", "Вера LiveTTS (Поддержка)"),
        ("denis", "Денис LiveTTS (Нейтральный)"),
        ("denis:casual", "Денис LiveTTS (Разговорный)"),
        ("denis:formal", "Денис LiveTTS (Формальный)"),
        ("denis:sales", "Денис LiveTTS (Продажи)"),
        ("vasily", "Василий LiveTTS (Поддержка)"),
        ("vasily:sales", "Василий LiveTTS (Продажи)"),
        ("sergey", "Сергей LiveTTS (Поддержка)"),
        ("sergey:sales", "Сергей LiveTTS (Продажи)"),
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
        ("dasha:good", "Даша (Радостный)"),
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
        ("zamira_ru", "Замира RU (Нейтральный)"),
        ("zamira_ru:friendly", "Замира RU (Дружелюбный)"),
        ("zamira_ru:strict", "Замира RU (Строгий)"),
        ("zhanar_ru", "Жанар RU (Нейтральный)"),
        ("zhanar_ru:friendly", "Жанар RU (Дружелюбный)"),
        ("zhanar_ru:strict", "Жанар RU (Строгий)"),
        ("saule_ru", "Сауле RU (Нейтральный)"),
        ("saule_ru:strict", "Сауле RU (Строгий)"),
        ("saule_ru:whisper", "Сауле RU (Шёпот)"),
        ("yulduz_ru", "Юлдуз RU (Нейтральный)"),
        ("yulduz_ru:friendly", "Юлдуз RU (Дружелюбный)"),
        ("yulduz_ru:strict", "Юлдуз RU (Строгий)"),
        ("yulduz_ru:whisper", "Юлдуз RU (Шёпот)"),
        ("madi_ru", "Мади RU"),
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
        ("saule:strict", "Saule (Strict)"),
        ("zhanar", "Zhanar"),
        ("zhanar:friendly", "Zhanar (Friendly)"),
    ],
    "uz-UZ": [
        ("nigora", "Nigora"),
        ("zamira", "Zamira"),
        ("zamira:friendly", "Zamira (Friendly)"),
        ("zamira:strict", "Zamira (Strict)"),
        ("lola", "Lola"),
        ("yulduz", "Yulduz"),
        ("yulduz:friendly", "Yulduz (Friendly)"),
        ("yulduz:strict", "Yulduz (Strict)"),
        ("yulduz:whisper", "Yulduz (Whisper)"),
    ],
    "he-IL": [
        ("naomi", "Naomi (Modern)"),
        ("naomi:classic", "Naomi (Classic)"),
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
    CONF_WEB_SEARCH: DEFAULT_WEB_SEARCH,
    CONF_STREAMING: DEFAULT_STREAMING,
    CONF_REASONING_EFFORT: DEFAULT_REASONING_EFFORT,
}

RECOMMENDED_STT_OPTIONS: dict[str, Any] = {
    CONF_STT_MODEL: DEFAULT_STT_MODEL,
    CONF_STT_LANGUAGE: DEFAULT_STT_LANGUAGE,
}

RECOMMENDED_TTS_OPTIONS: dict[str, Any] = {
    CONF_TTS_VOICE: DEFAULT_TTS_VOICE,
    CONF_TTS_EMOTION: DEFAULT_TTS_EMOTION,
    CONF_TTS_SPEED: DEFAULT_TTS_SPEED,
    CONF_TTS_PITCH_SHIFT: DEFAULT_TTS_PITCH_SHIFT,
}

RECOMMENDED_AI_TASK_OPTIONS: dict[str, Any] = {
    CONF_RECOMMENDED: True,
    CONF_CHAT_MODEL: DEFAULT_CHAT_MODEL,
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
    CONF_WEB_SEARCH: DEFAULT_WEB_SEARCH,
    CONF_REASONING_EFFORT: DEFAULT_REASONING_EFFORT,
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

