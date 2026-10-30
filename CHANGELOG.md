# Changelog

Все значимые изменения проекта документируются в этом файле.

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
