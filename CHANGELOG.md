# Changelog

Все значимые изменения проекта документируются в этом файле.

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
