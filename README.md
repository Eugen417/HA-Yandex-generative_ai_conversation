<p align="center">
  <img width="160" alt="Yandex AI Studio Logo" src="images/logo.png" />
</p>

<h1 align="center">Yandex AI Studio Integration for Home Assistant</h1>
<h2 align="center">Сделай свой умный дом по-настоящему умным с Яндекс!</h2>

<p align="center">
  <a href="https://github.com/hacs/integration"><img alt="hacs_badge" src="https://img.shields.io/badge/HACS-Default-41BDF5.svg" /></a>
  <a href="https://github.com/Eugen417/HA-Yandex-generative_ai_conversation/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/Eugen417/HA-Yandex-generative_ai_conversation" /></a>
  <a href="https://github.com/Eugen417/HA-Yandex-generative_ai_conversation/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/Eugen417/HA-Yandex-generative_ai_conversation/total" /></a>
  <a href="https://www.home-assistant.io/"><img alt="Home Assistant" src="https://img.shields.io/badge/Home%20Assistant-2025.8%2B%20%7C%202026.x-blue.svg" /></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg" /></a>
</p>

<p align="center">
  <b>🇷🇺 Русский</b> | <a href="README.en.md">🇬🇧 English</a>
</p>

Полнофункциональная интеграция **Yandex AI Studio (YandexGPT, YandexART и Yandex SpeechKit)** для **Home Assistant**, построенная по современной сервисной архитектуре `ConfigSubentry` и `ChatLog` (аналогично официальным интеграциям **Google Gemini** и **Ollama** и пользовательской [**Sber GigaChat AI**](https://github.com/Eugen417/HA-GigaChat-generative_ai_conversation)). Совместима с **Home Assistant 2025.8+ и 2026.x**.

Интеграция объединяет в одном подключении сразу **5 независимых ИИ-служб** для голосового ассистента **Assist** и автоматизаций умного дома:
1. 💬 **Диалоговая система (`Yandex AI Conversation`)** на базе **YandexGPT / AliceAI / Qwen3** с полноценным управлением умным домом (Tool Calling).
2. 🎙 **Распознавание речи (`Yandex AI STT`)** на базе **Yandex SpeechKit**.
3. 🔊 **Синтез речи (`Yandex AI TTS`)** на базе **Yandex SpeechKit** с выбором языка, голоса, эмоций (амплуа) и скорости речи.
4. 🧠 **Задача ИИ — текст, данные и Vision (`Yandex AI Task`)** — генерация текста, структурированных JSON-данных (**YandexGPT**) и мультимодальный анализ изображений/камер (**Gemma 3 27B Vision** — встроенный аналог `llmvision.image_analyzer`).
5. 🎨 **Задача ИИ — генерация изображений (`Yandex AI Task image`)** — создание изображений на базе **Alice AI ART (`aliceai-image-art-3.0`)**.

<p align="center">
  <img width="800" alt="Общий вид служб Yandex AI Studio в Home Assistant" src="images/services_overview.png" />
</p>

---

## ✨ Главные возможности

* 🧩 **Современная модульная архитектура (`Subentries`):** Как в интеграциях *Google Gemini* и *Ollama*, каждая служба (`Conversation`, `STT`, `TTS`, `AI Task`) является отдельным сервисным устройством со своей кнопкой настроек ⚙️. Вы также можете добавлять несколько диалоговых агентов (например, один для голосовых колонок, второй для Telegram-бота, третий для отчётов).
* 🏠 **Полноценное управление Умным Домом (Native Tool Calling):** Агент использует нативный механизм `ChatLog` и `llm.ToolInput` Home Assistant. При вопросах вроде *«Какая температура в спальне?»* или командах *«Включи свет на кухне»* модель вызывает инструменты Home Assistant (`GetLiveContext`, `HassTurnOn` и др.), получает реальные данные датчиков и формирует естественный человеческий ответ.
* 🎭 **Выбор голоса и эмоций TTS прямо в Assist (SpeechKit API v1 + API v3):** Поддержка как классических голосов Yandex SpeechKit (*Алёна, Филипп, Эрмил, Джейн, Мадирус, Омаж, Захар*), так и новых голосов 3-го поколения (*Даша, Юлия, Лера, Маша, Марина, Александр, Кирилл, Антон*) со всеми их амплуа (*Радостный, Дружелюбный, Строгий, Шёпот, Нейтральный, Раздраженный*) прямо в выпадающем списке пайплайна **Assist**.
* 🖼 **Разделённые службы AI Task + Vision-анализ камер (как в Google Gemini):**
  * **`Yandex AI Task`** — генерация текста/JSON-данных (`ai_task.generate_data`) и **анализ готовых изображений и камер (`SUPPORT_ATTACHMENTS`)** через мультимодальную модель **`gemma-3-27b-it/latest`** (штатная замена `llmvision.image_analyzer`).
  * **`Yandex AI Task image`** — генерация картинок (`ai_task.generate_image`) через новую модель **Alice AI ART (`aliceai-image-art-3.0`)**.
* 📊 **Учёт токенов и расчётных затрат (`sensor.py`, Beta):** В карточке каждой службы автоматически создаются диагностические сенсоры потраченных токенов, озвученных символов, сгенерированных изображений и ориентировочных затрат в рублях (`RUB`). *Функция работает в тестовом режиме и может не совпадать с фактическими списаниями в биллинге.*
* 🔍 **Встроенная диагностика (`diagnostics.py`):** Поддержка выгрузки диагностических данных конфигурации с автоматическим скрытием API-ключей.

---

## 🔑 Получение Folder ID и API-ключа

Перед установкой и настройкой интеграции вам понадобятся **Folder ID** и **API Key** от Yandex Cloud / Yandex AI Studio.

👉 **[Подробная пошаговая инструкция: Как получить Folder ID и API-ключ (API_KEY_GUIDE.md)](API_KEY_GUIDE.md)**

---

## 📦 Установка

### Вариант 1: Через HACS / Marketplace (Рекомендуется)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Eugen417&repository=HA-Yandex-generative_ai_conversation&category=integration)

1. Нажмите кнопку выше или откройте **HACS / Marketplace** в вашем Home Assistant.
2. Найдите в поиске **Yandex AI Studio**, нажмите **Скачать** и **перезагрузите Home Assistant**.

### Вариант 2: Ручная установка

1. Скачайте этот репозиторий (ZIP-архив).
2. Скопируйте папку `custom_components/yandex_generative_ai_conversation` в директорию `/config/custom_components/` вашего Home Assistant.
3. **Перезагрузите Home Assistant**.


---

## 🛠 Настройка в Home Assistant

### 1. Подключение интеграции
1. Перейдите в **Настройки -> Устройства и службы -> Добавить интеграцию**.
2. Введите в поиске **Yandex AI Studio**.
3. Укажите **Folder ID** и **API-ключ** (см. [инструкцию по их получению](API_KEY_GUIDE.md)).
4. После добавления интеграция автоматически создаст 5 базовых служб:
   - **Yandex AI Conversation** (Диалоговая система)
   - **Yandex AI STT** (Распознавание речи)
   - **Yandex AI TTS** (Преобразование текста в речь)
   - **Yandex AI Task** (Задача ИИ — текст, данные и Vision-анализ камер)
   - **Yandex AI Task image** (Задача ИИ — генерация изображений Alice AI ART)

При необходимости вы можете создавать дополнительные экземпляры любой из служб кнопками `+ Добавить диалоговую систему`, `+ Добавить службу распознавания речи`, `+ Добавить службу преобразования текста в речь`, `+ Добавить задачу ИИ (текст и данные)` и `+ Добавить задачу ИИ (генерация изображений)`.

---

### 2. Настройка диалоговой системы (`Yandex AI Conversation`)

Нажмите на значок шестерёнки ⚙️ напротив **Yandex AI Conversation**:
- **Инструкции (системный промпт):** Задайте характер и правила ответа ассистента.
- **AI tools (`llm_hass_api`):** Выберите **`Device control` (`Assist`)** (и при желании публичные MCP-серверы, например `HA-MCP Server`), чтобы разрешить модели управлять устройствами и читать их состояния.
  - ⚠️ **Важно про права `Home Assistant` и голосовые колонки:** системный пункт **`Home Assistant`** в списке `AI tools` даёт полный админский доступ ко всей системе и по правилам безопасности ядра Home Assistant (так же, как в *Google Gemini* и *Ollama*) работает **только у авторизованных администраторов в браузере или мобильном приложении**. На физических голосовых колонках и спутниках (*`ESP32-S3-Box-3`, `Home Assistant Voice PE`, `M5Stack Atom Echo`, `Wyoming`*) отсутствует админский `user_id`, поэтому при отмеченной галочке **`Home Assistant`** ядро HA отклонит запрос колонки с ошибкой `Error getting LLM API ...: Unauthorized`. Для голосовых колонок оставляйте галочку **`Home Assistant` снятой** (используйте `Device control`), а если нужен админский агент для браузера — добавьте второго агента кнопкой `+ Добавить диалоговую систему`.
  - Если вы создаёте отдельного чистого чат-бота для ВКонтакте или Telegram без доступа к управлению домом — просто очистите поле `AI tools`.
- **Поиск в интернете (`web_search`, по умолчанию Выкл):** Подключаемый инструмент **Yandex Search** (`GenSearch API v2` / `Responses API`). Рекомендуется **оставлять выключенным** у голосового агента управления домом (для максимальной скорости команд) и **включать** у второго агента для мессенджеров (ВКонтакте / Telegram), чтобы бот отвечал на вопросы о погоде, новостях, курсах валют и расписаниях.
- **Потоковый ответ (`streaming`, по умолчанию Вкл):** Передача текста по частям (SSE) в реальном времени — голосовой помощник Assist начинает озвучивать ответ с первых слов, не дожидаясь генерации всего текста.
- **Рекомендуемые настройки модели (`recommended`):** Когда переключатель включён (по умолчанию), используются оптимальные параметры (`yandexgpt/latest`, `temperature: 0.3`, `max_tokens: 2000`). При отключении открываются расширенные настройки (со списком моделей, автоматически дополняемым из `/v1/models`):
  - **Модель (`chat_model`):** `yandexgpt/latest`, `yandexgpt-lite/latest`, `aliceai-llm/latest`, `gemma-3-27b-it/latest`, `qwen3-235b-a22b-fp8/latest`, `yandexgpt/rc`, `yandexgpt-lite/rc` (или любой собственный URI модели).
  - **Режим рассуждений (`reasoning_effort`):** `none` (выключен), `low`, `medium`, `high` — глубина предварительных рассуждений для `Qwen3 235B` и новых моделей Яндекса.
  - **Температура и Max Tokens:** Тонкая настройка креативности и длины ответа.

<p align="center">
  <img width="460" alt="Настройки Yandex AI Conversation" src="images/conversation_settings.png" />
</p>

#### 💡 Для чего нужны Streaming, Поиск в интернете и Reasoning — и как они влияют на расход токенов?

| Опция | Для чего нужна и где полезна | Влияние на расход токенов и стоимость | Рекомендация |
| :--- | :--- | :--- | :--- |
| **Потоковый ответ (`SSE Streaming`)** | Передаёт слова по мере генерации, не дожидаясь конца абзаца. В голосовых колонках и спутниках **Assist** озвучка (`TTS`) стартует через **0.5–1 с** вместо 4–8 с тишины. Для ботов мессенджеров (`conversation.process`) разницы нет, так как ответ отправляется одним сообщением. | **0 ₽ / +0 токенов.** В биллинге Яндекса тарифицируется ровно то же число токенов, что и без стриминга. *(Техническая деталь: если выбранная модель не присылает финальный блок `usage` в SSE-потоке, сенсор в HA оценивает токены расчётно по длине текста; при `Выкл` всегда приходит точное число от сервера).* | Держать **Вкл** для голосового Assist. |
| **Поиск в интернете (`Yandex Search`)** | Позволяет модели самой запрашивать в Яндексе актуальную погоду, курсы валют ЦБ, новости, цены и расписания с возвратом кликабельных ссылок на источники (`sources`). | **В пассивном режиме** (когда поиск включён, но вопрос бытовой и модель его не вызывает): всего **~100 входных токенов** за описание инструмента.<br>**При срабатывании поиска:**<br>1) оплачивается сам поисковый запрос `GenSearch` (**~0.40 ₽**);<br>2) выполняется **второй проход к LLM**, куда передаётся найденная выдача (+500…2000 токенов) **и повторно весь системный промпт со списком устройств дома**! | **Выкл** на агенте управления домом (чтобы не гонять дважды огромный список лампочек и датчиков). **Вкл** на отдельном втором агенте для чата **ВК / Telegram** с очищенным полем `AI tools`. |
| **Режим рассуждений (`Reasoning`)** | Включает скрытую цепочку размышлений (`low` / `medium` / `high`) перед ответом у `Qwen3 235B` и новых моделей Яндекса. Повышает точность в сложных логических задачах и аналитике. | **Увеличивает расход в 2–5 раз.** Скрытые рассуждения (`reasoning_content`) не произносятся вслух, но тарифицируются Яндексом как полноценные выходные токены (`completion_tokens`), плюс замедляют первый ответ. | Держать **`none` (Выкл)** для обычного общения и голосовых команд; включать точечно для сложных задач `AI Task` / аналитики. |

---

### 3. Настройка синтеза речи (`Yandex AI TTS`)

Нажмите на значок шестерёнки ⚙️ напротив **Yandex AI TTS**:
- **Голос по умолчанию:** Выберите предпочтительный голос (*Алёна, Филипп, Эрмил, Джейн, Захар, Марина, Даша, Юлия, Лера, Маша, Александр, Кирилл, Антон* и др.).
- **Эмоция (амплуа):** `Радостный (good)`, `Нейтральный (neutral)` или `Раздраженный (evil)`.
- **Скорость речи:** От `0.1` до `3.0` (по умолчанию `1.0`).

<p align="center">
  <img width="600" alt="Настройки Yandex AI TTS" src="images/tts_settings.png" />
</p>

#### Доступные голоса и амплуа для `ru-RU` (SpeechKit v1 / v3 / LiveTTS):

| Голос | ID голоса | Пол | Поколение / Модель | Поддерживаемые амплуа (`role`) |
| :--- | :--- | :--- | :--- | :--- |
| **Ирина** | `irina` | Женский | **LiveTTS (v3)** | `neutral` *(по умолч.)*, `narrator`, `formal`, `support`, `sales` |
| **Софья / Вера** | `sofia`, `vera` | Женский | **LiveTTS (v3)** | `support` *(по умолч.)*, `casual` |
| **Денис** | `denis` | Мужской | **LiveTTS (v3)** | `neutral` *(по умолч.)*, `casual`, `formal`, `sales` |
| **Василий / Сергей** | `vasily`, `sergey` | Мужской | **LiveTTS (v3)** | `support` *(по умолч.)*, `sales` |
| **Даша / Юлия / Лера / Маша / Марина** | `dasha`, `julia`, `lera`, `masha`, `marina` | Женский | SpeechKit v3 | `neutral`, `good`, `friendly`, `strict`, `whisper` *(по голосу)* |
| **Александр / Кирилл / Антон** | `alexander`, `kirill`, `anton` | Мужской | SpeechKit v3 | `neutral`, `good`, `strict` *(по голосу)* |
| **Замира RU / Жанар RU / Сауле RU / Юлдуз RU / Мади RU** | `zamira_ru`, `zhanar_ru`, `saule_ru`, `yulduz_ru`, `madi_ru` | Ж / М | SpeechKit v3 | `neutral`, `friendly`, `strict`, `whisper` |
| **Алёна / Филипп / Эрмил / Джейн / Омаж / Захар / Мадирус** | `alena`, `filipp`, `ermil`, `jane`, `omazh`, `zahar`, `madirus` | Ж / М | SpeechKit v1 | `neutral`, `good`, `evil` *(по голосу)* |

*(Также поддерживаются языки `en-US` — `john`, `de-DE` — `lea`, `kk-KK` — `amira`, `madi`, `saule`, `zhanar`, `uz-UZ` — `nigora`, `zamira`, `lola`, `yulduz`, `he-IL` — `naomi` (`modern`, `classic`). Для голосов `LiveTTS` скорость и сдвиг высоты тона управляются самой нейросетью).*


---

### 4. Настройка голосового помощника (**Assist**)

1. Перейдите в **Настройки -> Голосовые помощники (Voice Assistants)**.
2. Создайте нового или откройте существующего ассистента (например, **Yandex**).
3. Выберите:
   - **Диалоговая система:** `Yandex AI Conversation`
   - *(Рекомендуется)* Включите переключатель **«Предпочитать локальную обработку команд»** — тогда простые типовые команды (*«включи/выключи свет»*) будут выполняться локально за 0 токенов, а сложные запросы пойдут в YandexGPT.
   - **Распознавание речи (STT):** `Yandex AI STT`
   - **Синтез речи (TTS):** `Yandex AI TTS` -> выберите язык `русский (Россия)` и нужный голос (или комбинацию `Голос (Эмоция)` прямо из выпадающего списка!). Поддерживается **сквозной потоковый синтез речи по предложениям (`async_stream_tts_audio`)** в бесшовный `WAV PCM` как для голосов v3, так и для классических голосов v1 — колонка начинает говорить первое предложение сразу по мере генерации текста моделью.

> ⚠️ **Напоминание для владельцев голосовых колонок (`ESP32-S3-Box-3`, `Home Assistant Voice PE`, `Atom Echo`, `Wyoming`):** убедитесь, что в настройках выбранного агента `Yandex AI Conversation` в поле **`AI tools`** отмечен **`Device control`**, но **снята** админская галочка **`Home Assistant`** — иначе ядро Home Assistant заблокирует голосовой запрос от устройства с ошибкой `Unauthorized`.

<p align="center">
  <img width="600" alt="Настройка пайплайна Assist" src="images/assist_pipeline.png" />
</p>

<p align="center">
  <img width="500" alt="Пример диалога в Assist" src="images/assist_chat.png" />
</p>

---

## 📊 Учёт токенов и расчётных затрат (Beta / Тестовый режим)

В карточке каждой из 5 служб интеграции автоматически создаются диагностические сенсоры (на базе `RestoreSensor` с сохранением накопленных показаний при перезагрузке Home Assistant):
- **`Yandex AI Conversation` и `Yandex AI Task`**:
  - **Потрачено токенов (`tokens`)** — общее число токенов (в атрибутах сенсора доступны `input_tokens`, `output_tokens`, `last_request_tokens`, `requests_count`, `last_model`).
  - **Затраты (`RUB`)** — ориентировочная стоимость запросов в рублях.
- **`Yandex AI Task image`**:
  - **Сгенерировано изображений (`img`)** и **Затраты (`RUB`)**.
- **`Yandex AI TTS`**:
  - **Озвучено символов (`chars`)** и **Затраты (`RUB`)**.
- **`Yandex AI STT`**:
  - **Распознано запросов (`req`)** и **Затраты (`RUB`)**.

> ⚠️ **Обратите внимание:** Учёт затрат в рублях работает **в тестовом (ознакомительном) порядке** и **может не совпадать с реальными списаниями** в вашем личном кабинете Yandex Cloud Billing. Расчёт выполняется локально по базовым публичным тарифам за токен/запрос и не учитывает стартовый грант (Trial), индивидуальные скидки, округления биллинга или возможные изменения прайс-листа Яндекса.

---

## 🎨 Использование AI Task (Генерация картинок и данных)

Интеграция создаёт две отдельные специализированные службы (по аналогии с Google Gemini):
- **`Yandex AI Task`** (`ai_task.yandex_ai_task`) — для генерации текста и структурированных данных (`ai_task.generate_data`) через **YandexGPT**.
- **`Yandex AI Task image`** (`ai_task.yandex_ai_task_image`) — для генерации изображений (`ai_task.generate_image`) через **Alice AI ART (`aliceai-image-art-3.0`)**.

### Пример 1: Генерация изображения через Alice AI ART (`ai_task.generate_image`)

```yaml
action: ai_task.generate_image
data:
  entity_id: ai_task.yandex_ai_task_image
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

### Пример 3: Анализ камер и изображений (Vision — аналог `llmvision.image_analyzer`)

Служба `Yandex AI Task` поддерживает флаг `SUPPORT_ATTACHMENTS` (прикрепление камер и изображений) и автоматически анализирует их через мультимодальную Vision-модель Яндекса **`gemma-3-27b-it/latest`**:

```yaml
action: ai_task.generate_data
data:
  entity_id: ai_task.yandex_ai_task
  task_name: "Анализ камеры у входа"
  instructions: "Опиши на русском языке, что происходит на камере. Есть ли люди или машины?"
  attachments:
    - media_content_id: media-source://camera/camera.vkhodnaia_dver
      media_content_type: image/jpeg
response_variable: camera_analysis
```

---

## 💬 Примеры автоматизаций: Чат-боты ВКонтакте и Telegram (с Поиском Яндекса)

Благодаря модульной архитектуре `Subentries` лучше всего разделить роли между двумя диалоговыми агентами в карточке интеграции **Yandex AI Studio**:
1. **`Yandex AI Conversation`** (для голосовых колонок и Assist): `AI tools = Assist`, **`Поиск в интернете = Выкл`** — мгновенное управление светом, климатом и датчиками без лишних задержек.
2. Нажмите **`+ Добавить диалоговую систему`**, назовите её **`Yandex Бот Чата`** (`conversation.yandex_bot_chata`): очистите `AI tools` (или оставьте нужные), включите **`Поиск в интернете (Yandex Search) = Вкл`** и выберите модель (например, живую `aliceai-llm/latest`, мощную `qwen3-235b-a22b-fp8/latest` или экономичную `yandexgpt-lite/latest`). *(Не забудьте выдать сервисному аккаунту роль `search-api.webSearch.user` — см. [API_KEY_GUIDE.md](API_KEY_GUIDE.md)).*

<p align="center">
  <img width="390" alt="Пример работы Поиска Яндекса — погода" src="images/assist_web_search_weather.png" />
  <img width="390" alt="Пример работы Поиска Яндекса — курс валют со ссылками" src="images/assist_web_search_rates.png" />
</p>

### Пример 1: ИИ-чат во ВКонтакте (текст + голосовые сообщения + веб-поиск) через [VK Notify](https://github.com/Eugen417/ha_vk_notify_plus)

Интеграция **VK Notify** в режиме Long Poll принимает как обычные сообщения (`text`), так и готовые расшифровки голосовых сообщений (`transcript`), умеет показывать статус *«печатает...»* и цитировать исходное сообщение (`reply_to`):

```yaml
alias: "ВК: Умный чат-бот Yandex AI (живой диалог в ЛС + по имени Бот190 в беседе)"
description: "В личке отвечает сразу живым диалогом, а в групповой беседе — только при обращении 'Бот190' / 'бот 190'"
mode: queued
max: 10
triggers:
  - trigger: event
    event_type: vk_notify_text
variables:
  raw_query: >-
    {{ (trigger.event.data.text
        if (trigger.event.data.text | default('') | trim) != ''
        else (trigger.event.data.transcript | default(''))) | trim }}
  is_private_chat: "{{ (trigger.event.data.peer_id | int(0)) < 2000000000 }}"
  wake_pattern: "^(?:\\[club\\d+\\|[^\\]]+\\]\\s*)?бот\\s*190\\b[,:\\s-]*"
  is_addressed_to_bot: "{{ raw_query is search(wake_pattern, ignorecase=True) }}"
  clean_query: >-
    {{ (raw_query | regex_replace(wake_pattern, '', ignorecase=True) | trim)
       if is_addressed_to_bot else raw_query }}
conditions:
  # 1. Защита от чужих чатов (отсекаем не привязанные в VK Notify диалоги)
  - condition: template
    value_template: "{{ trigger.event.data.entity_id != 'not_configured' }}"
  # 2. Белый список VK ID пользователей (укажите свои числовые from_id из ВК)
  - condition: template
    value_template: "{{ trigger.event.data.from_id in [123456789, 987654321] }}"
  # 3. В личке — отвечаем сразу; в групповой беседе — только при обращении "Бот190"
  - condition: template
    value_template: "{{ clean_query != '' and (is_private_chat or is_addressed_to_bot) }}"
actions:
  - action: vk_notify.set_activity
    target:
      entity_id: "{{ trigger.event.data.entity_id }}"
    data:
      type: typing
  - action: conversation.process
    data:
      agent_id: conversation.yandex_bot_chata
      text: "{{ clean_query }}"
      conversation_id: "vk_{{ trigger.event.data.peer_id }}"
    response_variable: ai_reply
  - action: vk_notify.send_message
    target:
      entity_id: "{{ trigger.event.data.entity_id }}"
    data:
      message: "{{ ai_reply.response.speech.plain.speech }}"
      parse_mode: markdownv2
      reply_to: "{{ trigger.event.data.conversation_message_id }}"
```

### Пример 2: Команда `/камера` во ВКонтакте — снимок + ИИ-описание от Gemma 3 Vision

```yaml
alias: "ВК: Осмотр камеры по команде /камера"
mode: queued
triggers:
  - trigger: event
    event_type: vk_notify_command
    event_data:
      command: "камера"
conditions:
  - condition: template
    value_template: >-
      {{ trigger.event.data.entity_id != 'not_configured'
         and trigger.event.data.from_id in [123456789, 987654321] }}
actions:
  - action: vk_notify.set_activity
    target:
      entity_id: "{{ trigger.event.data.entity_id }}"
    data:
      type: typing
  - action: ai_task.generate_data
    data:
      entity_id: ai_task.yandex_ai_task
      task_name: "Осмотр двора"
      instructions: "Кратко опиши на русском языке, что сейчас видно на камере, есть ли люди, машины или курьеры."
      attachments:
        - media_content_id: media-source://camera/camera.front_door
          media_content_type: image/jpeg
    response_variable: cam_report
  - action: vk_notify.send_photo
    target:
      entity_id: "{{ trigger.event.data.entity_id }}"
    data:
      camera_entity: camera.front_door
      message: "📷 **Отчёт ИИ по камере:**\n{{ cam_report.data }}"
      parse_mode: markdownv2
      reply_to: "{{ trigger.event.data.conversation_message_id }}"
```

### Пример 3: ИИ-чат в Telegram (`telegram_bot`) с Поиском Яндекса и историей диалога

```yaml
alias: "Telegram: Чат-бот Yandex AI Studio (живой диалог в ЛС + по имени Бот190 в группе)"
description: "В личном чате отвечает сразу, а в группе — при обращении 'Бот190'"
mode: queued
max: 10
triggers:
  - trigger: event
    event_type: telegram_text
variables:
  raw_query: "{{ trigger.event.data.text | default('') | trim }}"
  is_private_chat: "{{ (trigger.event.data.chat_id | int(0)) > 0 }}"
  wake_pattern: "^(?:@\\w+\\s*)?бот\\s*190\\b[,:\\s-]*"
  is_addressed_to_bot: "{{ raw_query is search(wake_pattern, ignorecase=True) }}"
  clean_query: >-
    {{ (raw_query | regex_replace(wake_pattern, '', ignorecase=True) | trim)
       if is_addressed_to_bot else raw_query }}
conditions:
  # Белый список разрешённых Telegram user_id
  - condition: template
    value_template: "{{ trigger.event.data.user_id in [111222333, 444555666] }}"
  # В ЛС — живой разговор; в группе — только при обращении "Бот190"
  - condition: template
    value_template: "{{ clean_query != '' and (is_private_chat or is_addressed_to_bot) }}"
actions:
  - action: telegram_bot.send_chat_action
    data:
      chat_id: "{{ trigger.event.data.chat_id }}"
      chat_action: typing
  - action: conversation.process
    data:
      agent_id: conversation.yandex_bot_chata
      text: "{{ clean_query }}"
      conversation_id: "tg_{{ trigger.event.data.chat_id }}"
    response_variable: ai_reply
  - action: telegram_bot.send_message
    data:
      chat_id: "{{ trigger.event.data.chat_id }}"
      message: "{{ ai_reply.response.speech.plain.speech }}"
      parse_mode: plain_text
      reply_to_message_id: "{{ trigger.event.data.id }}"
```

---

## 📂 Структура репозитория

```text
HA-Yandex-generative_ai_conversation/
├── .github/workflows/          # GitHub Actions (Hassfest & HACS Validation, Release)
├── custom_components/
│   └── yandex_generative_ai_conversation/
│       ├── __init__.py         # Инициализация интеграции и управление Subentries
│       ├── ai_task.py          # Платформа AI Task (YandexGPT + YandexART)
│       ├── brand/              # Локальные иконки и логотипы интеграции (icon.png, logo.png)
│       ├── config_flow.py      # Мастер настройки и ConfigSubentryFlow
│       ├── const.py            # Константы, модели и список голосов/эмоций
│       ├── conversation.py     # Диалоговый агент для Assist
│       ├── diagnostics.py      # Диагностика интеграции с маскированием ключей
│       ├── entity.py           # Базовый класс LLM, SSE-стриминг и цикл Tool Calling
│       ├── helpers.py          # Авторизация (Api-Key/IAM), /v1/models и Yandex Search API
│       ├── manifest.json       # Манифест интеграции
│       ├── sensor.py           # Сенсоры учёта токенов, запросов и расчётных затрат (RUB)
│       ├── strings.json        # Строки локализации
│       ├── stt.py              # Распознавание речи (Yandex SpeechKit STT)
│       ├── tts.py              # Синтез речи (Yandex SpeechKit TTS v1 + v3)
│       └── translations/       # Переводы (ru.json, en.json)
├── images/                     # Папка для скриншотов документации
├── API_KEY_GUIDE.md            # Пошаговая инструкция по получению Folder ID и API-ключа
├── CHANGELOG.md                # История изменений
├── LICENSE                     # Лицензия MIT
├── README.en.md                # Документация на английском языке (English documentation)
├── README.md                   # Основная документация
└── hacs.json                   # Конфигурация HACS
```

---

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT License**. Подробности в файле [LICENSE](LICENSE).

