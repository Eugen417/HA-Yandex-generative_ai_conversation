# 🤖 Yandex AI Studio Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.7%2B%20%7C%202026.x-blue.svg)](https://www.home-assistant.io/)

Полнофункциональная интеграция **Yandex AI Studio (YandexGPT, YandexART и Yandex SpeechKit)** для **Home Assistant**, построенная по современной сервисной архитектуре `ConfigSubentry` и `ChatLog` (аналогично официальным интеграциям **Google Gemini** и **Ollama** в Home Assistant 2026).

Интеграция объединяет в одном подключении сразу **4 независимые ИИ-службы** для голосового ассистента **Assist** и автоматизаций умного дома:
1. 💬 **Диалоговая система (Conversation)** на базе **YandexGPT / AliceAI / Qwen3** с полноценным управлением умным домом (Tool Calling).
2. 🎙 **Распознавание речи (STT)** на базе **Yandex SpeechKit**.
3. 🔊 **Синтез речи (TTS)** на базе **Yandex SpeechKit** с выбором языка, голоса, эмоций (амплуа) и скорости речи.
4. 🎨 **Задачи ИИ (AI Task)** — генерация текста/структурированных JSON-данных (**YandexGPT**) и генерация изображений (**YandexART**).

<p align="center">
  <img width="800" alt="Общий вид служб Yandex AI Studio в Home Assistant" src="images/services_overview.png" />
</p>

---

## ✨ Главные возможности

* 🧩 **Современная модульная архитектура (`Subentries`):** Как в интеграциях *Google Gemini* и *Ollama*, каждая служба (`Conversation`, `STT`, `TTS`, `AI Task`) является отдельным сервисным устройством со своей кнопкой настроек ⚙️. Вы также можете добавлять несколько диалоговых агентов (например, один для голосовых колонок, второй для Telegram-бота, третий для отчётов).
* 🏠 **Полноценное управление Умным Домом (Native Tool Calling):** Агент использует нативный механизм `ChatLog` и `llm.ToolInput` Home Assistant. При вопросах вроде *«Какая температура в спальне?»* или командах *«Включи свет на кухне»* модель вызывает инструменты Home Assistant (`GetLiveContext`, `HassTurnOn` и др.), получает реальные данные датчиков и формирует естественный человеческий ответ.
* 🎭 **Выбор голоса и эмоций TTS прямо в Assist:** Поддержка всех голосов Yandex SpeechKit (*Алёна, Филипп, Эрмил, Джейн, Мадирус, Омаж, Захар, Даша, Юлия, Лера, Маша, Марина, Александр, Кирилл, Антон* и др.) и эмоциональных окрасок (*Радостный, Нейтральный, Раздраженный*) как в настройках службы, так и прямо в выпадающем списке пайплайна **Assist**.
* 🖼 **Генерация картинок (YandexART) и данных (AI Task):** Поддержка платформы `ai_task` (`ai_task.generate_image` и `ai_task.generate_data`) для создания изображений по текстовому описанию и анализа данных в автоматизациях.
* 🔍 **Встроенная диагностика (`diagnostics.py`):** Поддержка выгрузки диагностических данных конфигурации с автоматическим скрытием API-ключей.

---

## 🔑 Получение Folder ID и API-ключа

Перед установкой и настройкой интеграции вам понадобятся **Folder ID** и **API Key** от Yandex Cloud / Yandex AI Studio.

👉 **[Подробная пошаговая инструкция: Как получить Folder ID и API-ключ (API_KEY_GUIDE.md)](API_KEY_GUIDE.md)**

---

## 📦 Установка

### Вариант 1: Через HACS (Рекомендуется)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Eugen417&repository=HA-Yandex-generative_ai_conversation&category=integration)

1. Откройте **HACS** в вашем Home Assistant.
2. Нажмите на три точки в правом верхнем углу -> **Пользовательские репозитории** (*Custom repositories*).
3. Вставьте ссылку на этот репозиторий:
   `https://github.com/Eugen417/HA-Yandex-generative_ai_conversation`
4. Выберите категорию **Интеграция** (*Integration*) и нажмите **Добавить**.
5. Найдите **Yandex AI Studio** в списке HACS и нажмите **Скачать**.
6. **Перезагрузите Home Assistant**.

### Вариант 2: Ручная установка

1. Скачайте этот репозиторий (ZIP-архив).
2. Скопируйте папку `custom_components/Yandex-generative_ai_conversation` в директорию `/config/custom_components/` вашего Home Assistant.
3. **Перезагрузите Home Assistant**.


---

## 🛠 Настройка в Home Assistant

### 1. Подключение интеграции
1. Перейдите в **Настройки -> Устройства и службы -> Добавить интеграцию**.
2. Введите в поиске **Yandex AI Studio**.
3. Укажите **Folder ID** и **API-ключ** (см. [инструкцию по их получению](API_KEY_GUIDE.md)).
4. После добавления интеграция автоматически создаст 4 базовые службы:
   - **Yandex AI Conversation** (Диалоговая система)
   - **Yandex AI STT** (Распознавание речи)
   - **Yandex AI TTS** (Преобразование текста в речь)
   - **Yandex AI Task** (Задача ИИ)

При необходимости вы можете создавать дополнительные экземпляры любой из служб кнопками `+ Добавить диалоговую систему`, `+ Добавить службу распознавания речи`, `+ Добавить службу преобразования текста в речь` и `+ Добавить задачу ИИ`.

---

### 2. Настройка диалоговой системы (`Yandex AI Conversation`)

Нажмите на значок шестерёнки ⚙️ напротив **Yandex AI Conversation**:
- **Инструкции (системный промпт):** Задайте характер и правила ответа ассистента.
- **Управление Home Assistant (`llm_hass_api`):** Выберите **Assist** (а также при желании дополнительные LLM API, например MCP Tools), чтобы разрешить модели управлять устройствами и читать их состояния.
- **Модель (`chat_model`):**
  - `yandexgpt/latest` — основная флагманская модель YandexGPT Pro;
  - `yandexgpt-lite/latest` — быстрая и лёгкая модель;
  - `yandexgpt/rc` / `yandexgpt-lite/rc` — релиз-кандидаты новых версий;
  - `aliceai-llm/latest` — модель Alice AI;
  - `qwen3-235b-a22b-fp8/latest` — модель Qwen3 в Yandex AI Studio (также поддерживается ввод любого собственного названия модели).
- **Температура и Max Tokens:** Тонкая настройка креативности и длины ответа.

<p align="center">
  <img width="600" alt="Настройки Yandex AI Conversation" src="images/conversation_settings.png" />
</p>

---

### 3. Настройка синтеза речи (`Yandex AI TTS`)

Нажмите на значок шестерёнки ⚙️ напротив **Yandex AI TTS**:
- **Голос по умолчанию:** Выберите предпочтительный голос (*Алёна, Филипп, Эрмил, Джейн, Захар, Марина, Даша, Юлия, Лера, Маша, Александр, Кирилл, Антон* и др.).
- **Эмоция (амплуа):** `Радостный (good)`, `Нейтральный (neutral)` или `Раздраженный (evil)`.
- **Скорость речи:** От `0.1` до `3.0` (по умолчанию `1.0`).

<p align="center">
  <img width="600" alt="Настройки Yandex AI TTS" src="images/tts_settings.png" />
</p>

#### Доступные голоса и эмоции для `ru-RU`:

| Голос | ID голоса | Пол | Поддерживаемые эмоции |
| :--- | :--- | :--- | :--- |
| **Алёна** | `alena` | Женский | `neutral`, `good` |
| **Филипп** | `filipp` | Мужской | `neutral` |
| **Эрмил** | `ermil` | Мужской | `neutral`, `good` |
| **Джейн** | `jane` | Женский | `neutral`, `good`, `evil` |
| **Омаж** | `omazh` | Женский | `neutral`, `evil` |
| **Захар** | `zahar` | Мужской | `neutral`, `good` |
| **Мадирус** | `madirus` | Мужской | `neutral` |
| **Даша / Юлия / Лера / Маша / Марина** | `dasha`, `julia`, `lera`, `masha`, `marina` | Женский | `neutral` |
| **Александр / Кирилл / Антон** | `alexander`, `kirill`, `anton` | Мужской | `neutral` |

*(Также поддерживаются языки `en-US` — `john`, `de-DE` — `lea`, `kk-KK` — `amira`, `madi`, `saule`, `zhanar`, `uz-UZ` — `nigora`, `lola`, `yulduz`, `he-IL` — `naomi`).*


---

### 4. Настройка голосового помощника (**Assist**)

1. Перейдите в **Настройки -> Голосовые помощники (Voice Assistants)**.
2. Создайте нового или откройте существующего ассистента (например, **Yandex**).
3. Выберите:
   - **Диалоговая система:** `Yandex AI Conversation`
   - **Распознавание речи (STT):** `Yandex AI STT`
   - **Синтез речи (TTS):** `Yandex AI TTS` -> выберите язык `русский (Россия)` и нужный голос (или комбинацию `Голос (Эмоция)` прямо из выпадающего списка!).

<p align="center">
  <img width="600" alt="Настройка пайплайна Assist" src="images/assist_pipeline.png" />
</p>

<p align="center">
  <img width="500" alt="Пример диалога в Assist" src="images/assist_chat.png" />
</p>

---

## 🎨 Использование AI Task (Генерация картинок и данных)

Служба **Yandex AI Task** предоставляет сущность `ai_task.yandex_ai_task`, которую можно вызывать в автоматизациях и скриптах Home Assistant:

### Пример 1: Генерация изображения через YandexART (`ai_task.generate_image`)

```yaml
action: ai_task.generate_image
data:
  entity_id: ai_task.yandex_ai_task
  task_name: "Погода на сегодня"
  instructions: "Уютный умный дом в осеннем лесу, мягкий тёплый свет в окнах, кинематографичный стиль"
response_variable: generated_image
```

### Пример 2: Генерация структурированных данных через YandexGPT (`ai_task.generate_data`)

```yaml
action: ai_task.generate_data
data:
  entity_id: ai_task.yandex_ai_task
  task_name: "Краткая сводка по дому"
  instructions: "Составь краткую сводку для утреннего приветствия на основе погоды и температуры в спальне."
response_variable: summary
```

---

## 📂 Структура репозитория

```text
HA-Yandex-generative_ai_conversation/
├── .github/workflows/          # GitHub Actions (Hassfest & HACS Validation, Release)
├── custom_components/
│   └── Yandex-generative_ai_conversation/
│       ├── __init__.py         # Инициализация интеграции и управление Subentries
│       ├── ai_task.py          # Платформа AI Task (YandexGPT + YandexART)
│       ├── config_flow.py      # Мастер настройки и ConfigSubentryFlow
│       ├── const.py            # Константы, модели и список голосов/эмоций
│       ├── conversation.py     # Диалоговый агент для Assist
│       ├── diagnostics.py      # Диагностика интеграции с маскированием ключей
│       ├── entity.py           # Базовый класс LLM и цикл Tool Calling через ChatLog
│       ├── manifest.json       # Манифест интеграции
│       ├── strings.json        # Строки локализации
│       ├── stt.py              # Распознавание речи (Yandex SpeechKit STT)
│       ├── tts.py              # Синтез речи (Yandex SpeechKit TTS)
│       └── translations/       # Переводы (ru.json, en.json)
├── images/                     # Папка для скриншотов документации
├── API_KEY_GUIDE.md            # Пошаговая инструкция по получению Folder ID и API-ключа
├── CHANGELOG.md                # История изменений
├── LICENSE                     # Лицензия MIT
├── README.md                   # Основная документация
└── hacs.json                   # Конфигурация HACS
```

---

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT License**. Подробности в файле [LICENSE](LICENSE).

