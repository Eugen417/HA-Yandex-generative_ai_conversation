# Changelog

Все значимые изменения проекта документируются в этом файле.

## [1.2.5] - 2026-11-17

### Обновлено
- **`hacs.json` и документация**: минимальная требуемая версия Home Assistant уточнена до **`2025.8.0`** (первый релиз с платформой `ai_task` — по рекомендации `@frenck` при включении интеграции в официальный каталог **HACS Default**).

## [1.2.4] - 2026-11-16

### Добавлено
- **Документация на английском языке (`README.en.md`)** и переключатель языка (`🇷🇺 Русский | 🇬🇧 English`) в шапке документации для публикации в официальном каталоге HACS.

## [1.2.3] - 2026-11-16

### Исправлено и улучшено
- **Обратная совместимость с Home Assistant `2025.7`–`2026.8` и `2026.9+` (`entity.py`)**: добавлен автоматический фоллбэк с `probatio.to_openapi` на `voluptuous_openapi.convert`, устраняющий ошибки `No module named 'probatio'` и `Platform ...conversation not found` на версиях HA до `2026.9`.
- **Общий пул HTTP/TLS-сессий Home Assistant (`async_get_clientsession`)**: все платформы (`entity.py`, `ai_task.py`, `stt.py`, `tts.py`) переведены на переиспользование соединений ядра HA, что ускоряет отклик ассистента.
- **Чистка предупреждений HA 2027.8 и точность сенсоров (`__init__.py`, `config_flow.py`, `sensor.py`)**:
  - Заменён устаревший вызов `device_registry.async_get_device` на `async_entries_for_config_entry` в `__init__.py` и убрана двойная перезагрузка в `config_flow.py`.
  - Устранено накопление погрешности округления в сенсоре затрат (`sensor.py`).

## [1.2.2] - 2026-11-09

### Исправлено и улучшено
- **Мультивыбор инструментов ИИ (`AI tools` / `llm_hass_api`) по аналогии с Google Gemini и Ollama**:
  - Устранён принудительный сброс списка `llm_hass_api` при выборе нескольких провайдеров одновременно (теперь `Device control`, `Home Assistant`, `HA-MCP Server (tool search)` и другие MCP-серверы сохраняются и работают вместе).
  - Добавлена дедупликация имён инструментов при объединении нескольких LLM API в `entity.py`.
  - Добавлены описания полей (`data_description`) в настройках диалогового агента (`translations/ru.json` и `translations/en.json`), поясняющие разницу между `Device control` и `Home Assistant`.

## [1.2.1] - 2026-11-01

### Исправлено
- **`Yandex AI Task` / `Yandex AI Conversation` (`entity.py`)**: исправлена ошибка `400 unknown model 'gpt://gemma-3-27b-it/latest'` при вызове текстовых задач `ai_task.generate_data` без вложений камер, когда в настройках службы выбрана мультимодальная модель `gemma-3-27b-it/latest` или `qwen3-235b-a22b-fp8/latest`. Теперь для текстовых запросов без картинок автоматически используется `yandexgpt/latest`, а для анализа камер (`attachments`) — `gemma-3-27b-it/latest` через `/v1/chat/completions`.
- **`manifest.json`**: очищено поле `requirements` для успешного прохождения валидации Home Assistant Hassfest.

## [1.2.0] - 2026-10-30

### Добавлено
- Разделение служб **AI Task** по образцу Google Gemini:
  - **`Yandex AI Task`** (`ai_task_data`) — генерация текста, структурированных JSON-данных и анализ вложений/камер (`SUPPORT_ATTACHMENTS`).
  - **`Yandex AI Task image`** (`ai_task_image`) — генерация изображений через новую модель **Alice AI ART (`aliceai-image-art-3.0`)** и синхронный эндпоинт `https://ai.api.cloud.yandex.net/v1/images/generations`.
- Мультимодальный анализ изображений и камер (Vision — штатный аналог `llmvision.image_analyzer`) в `ai_task.generate_data` через модель **`gemma-3-27b-it/latest`**.
- Платформа диагностических сенсоров **`sensor.py`** (в тестовом режиме) для каждой службы: счётчики потраченных токенов, сгенерированных изображений, озвученных символов, запросов STT и расчётных затрат в рублях (`RUB`) с сохранением состояния (`RestoreSensor`).
- Поддержка голосов 3-го поколения Yandex SpeechKit (**API v3** `/tts/v3/utteranceSynthesis`: *Даша, Юлия, Лера, Маша, Марина, Александр, Кирилл, Антон* и др.) со всеми эмоциональными ролями (`friendly`, `strict`, `whisper`, `good`, `neutral`).
- Динамическое скрытие/отображение расширенных настроек модели по переключателю **«Рекомендуемые настройки модели»** (по аналогии с Google Gemini).

## [1.1.0] - 2026-10-29

### Добавлено
- Архитектура дочерних служб (`ConfigSubentry`) по образцу `Google Gemini` и `Ollama`:
  - **Yandex AI Conversation** — диалоговый агент на базе YandexGPT (`yandexgpt/latest`, `yandexgpt-lite/latest`, `yandexgpt/rc`, `aliceai-llm/latest`, `qwen3-235b-a22b-fp8/latest`).
  - **Yandex AI STT** — распознавание речи Yandex SpeechKit с выбором модели и языка.
  - **Yandex AI TTS** — синтез речи Yandex SpeechKit с выбором языка, голоса, эмоционального амплуа (`good`, `neutral`, `evil`) и скорости речи прямо в настройках службы и в пайплайне Assist.
  - **Yandex AI Task** — поддержка задач ИИ (`ai_task`): генерация текста/структурированных данных (YandexGPT) и генерация изображений (YandexART `yandex-art/latest`).
- Полноценный цикл вызова инструментов (Tool Calling) через `ChatLog` Home Assistant: результаты выполнения команд и получения контекста (`GetLiveContext`, `HassTurnOn` и др.) возвращаются в модель для формирования естественного ответа.
- Поддержка диагностики (`diagnostics.py`) со скрытием секретных ключей.
- Полная локализация интерфейса настроек на русский и английский языки.
