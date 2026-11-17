<p align="center">
  <img width="160" alt="Yandex AI Studio Logo" src="images/logo.png" />
</p>

<h1 align="center">Yandex AI Studio Integration for Home Assistant</h1>
<h2 align="center">Make your smart home truly intelligent with Yandex AI Studio!</h2>

<p align="center">
  <a href="https://github.com/hacs/integration"><img alt="hacs_badge" src="https://img.shields.io/badge/HACS-Default-41BDF5.svg" /></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg" /></a>
  <a href="https://www.home-assistant.io/"><img alt="Home Assistant" src="https://img.shields.io/badge/Home%20Assistant-2025.8%2B%20%7C%202026.x-blue.svg" /></a>
</p>

<p align="center">
  <a href="README.md">🇷🇺 Русский</a> | <b>🇬🇧 English</b>
</p>

A full-featured **Yandex AI Studio (YandexGPT, Alice AI ART, Gemma 3 Vision, and Yandex SpeechKit)** custom integration for **Home Assistant**, built on the modern `ConfigSubentry` and `ChatLog` service architecture (aligned with official **Google Gemini** and **Ollama** integrations, as well as [**Sber GigaChat AI**](https://github.com/Eugen417/HA-GigaChat-generative_ai_conversation) in Home Assistant 2026).

The integration combines **5 independent AI sub-services** under a single integration entry for **Assist** voice pipelines and smart home automations:

1. 💬 **Conversation Agent (`Yandex AI Conversation`)** powered by **YandexGPT / AliceAI / Qwen3** with full smart home control (Native Tool Calling).
2. 🎙 **Speech-to-Text (`Yandex AI STT`)** powered by **Yandex SpeechKit**.
3. 🔊 **Text-to-Speech (`Yandex AI TTS`)** powered by **Yandex SpeechKit** (API v1 + API v3) with selectable language, voice, emotion/role, and speech speed.
4. 🧠 **AI Task — Text, Structured Data & Vision (`Yandex AI Task`)** — text generation, structured JSON output (**YandexGPT**), and multimodal camera/image analysis (**Gemma 3 27B Vision** — a built-in replacement for `llmvision.image_analyzer`).
5. 🎨 **AI Task — Image Generation (`Yandex AI Task image`)** — image creation powered by **Alice AI ART (`aliceai-image-art-3.0`)**.

<p align="center">
  <img width="800" alt="Overview of Yandex AI Studio services in Home Assistant" src="images/services_overview.png" />
</p>

---

## ✨ Key Features

* 🧩 **Modern Modular Architecture (`Subentries`):** Just like *Google Gemini* and *Ollama*, each service (`Conversation`, `STT`, `TTS`, `AI Task`, `AI Task image`) is an independent service device with its own settings button ⚙️. You can add multiple conversation agents (e.g., one for smart speakers, another for Telegram bots, and a third for daily digests).
* 🏠 **Full Smart Home Control (Native Tool Calling):** Uses Home Assistant's native `ChatLog` and `llm.ToolInput` pipeline. When asked *"What is the bedroom temperature?"* or *"Turn on the kitchen lights"*, the model invokes Home Assistant tools (`GetLiveContext`, `HassTurnOn`, MCP tools, etc.), reads live states, and responds naturally. Supports selecting multiple LLM tool providers simultaneously.
* 🎭 **TTS Voice & Emotion Selection Directly in Assist (SpeechKit API v1 + API v3):** Supports both classic Yandex SpeechKit voices (*Alena, Filipp, Ermil, Jane, Madirus, Omazh, Zahar*) and 3rd-generation voices (*Dasha, Julia, Lera, Masha, Marina, Alexander, Kirill, Anton*) along with emotional roles (*Good/Joyful, Friendly, Strict, Whisper, Neutral, Evil*) right from the **Assist** pipeline dropdown.
* 🖼 **Dedicated AI Task Entities + Camera Vision:**
  * **`Yandex AI Task`** — text/JSON generation (`ai_task.generate_data`) and **camera/image analysis (`SUPPORT_ATTACHMENTS`)** powered by **`gemma-3-27b-it/latest`**.
  * **`Yandex AI Task image`** — image generation (`ai_task.generate_image`) powered by **Alice AI ART (`aliceai-image-art-3.0`)**.
* 📊 **Token & Estimated Cost Tracking (`sensor.py`, Beta):** Automatically creates persistent diagnostic sensors (`RestoreSensor`) for tokens, TTS characters, STT requests, generated images, and approximate cost in `RUB`.
* 🔍 **Built-in Diagnostics (`diagnostics.py`):** Exports configuration diagnostics with automatic redaction of secret API keys.

---

## 🔑 Obtaining Folder ID & API Key

Before installing and configuring the integration, you will need a **Folder ID** and an **API Key** from Yandex Cloud / Yandex AI Studio.

👉 **[Step-by-Step Illustrated Guide: How to Obtain Folder ID and API Key (API_KEY_GUIDE.md)](API_KEY_GUIDE.md)**

---

## 📦 Installation

### Option 1: Via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Eugen417&repository=HA-Yandex-generative_ai_conversation&category=integration)

1. Open **HACS** in your Home Assistant instance.
2. Go to **Integrations** -> search for **Yandex AI Studio** (or add `https://github.com/Eugen417/HA-Yandex-generative_ai_conversation` via **Custom repositories** under category **Integration**).
3. Click **Download** and **restart Home Assistant**.

### Option 2: Manual Installation

1. Download this repository (ZIP archive).
2. Copy `custom_components/yandex_generative_ai_conversation` into your Home Assistant `/config/custom_components/` directory.
3. **Restart Home Assistant**.

---

## 🛠 Configuration in Home Assistant

### 1. Adding the Integration
1. Go to **Settings -> Devices & Services -> Add Integration** and search for **Yandex AI Studio**.
2. Enter your **Folder ID** and **API Key** (see [API_KEY_GUIDE.md](API_KEY_GUIDE.md)).
3. Five default sub-services are created automatically:
   - **Yandex AI Conversation** (Conversation agent)
   - **Yandex AI STT** (Speech-to-Text)
   - **Yandex AI TTS** (Text-to-Speech)
   - **Yandex AI Task** (AI Task — text, structured data & camera Vision)
   - **Yandex AI Task image** (AI Task — Alice AI ART image generation)

You can add extra instances of any service at any time using the `+ Add ...` buttons on the integration page.

### 2. Conversation Agent Settings (`Yandex AI Conversation`)
Click the gear icon ⚙️ next to **Yandex AI Conversation**:
- **Instructions (System Prompt):** Customize the assistant's persona and behavior.
- **Control Home Assistant (`llm_hass_api`):** Select **Assist** (and optionally additional LLM tool providers such as MCP Servers) to let the model read entity states and control devices.
- **Recommended model settings (`recommended`):** Enabled by default (`yandexgpt/latest`, `temperature: 0.3`, `max_tokens: 2000`). Uncheck to manually configure:
  - **Model (`chat_model`):** `yandexgpt/latest`, `yandexgpt-lite/latest`, `aliceai-llm/latest`, `gemma-3-27b-it/latest`, `qwen3-235b-a22b-fp8/latest`, `yandexgpt/rc`, `yandexgpt-lite/rc` (or any custom model URI).
  - **Temperature & Max Tokens.**

<p align="center">
  <img width="600" alt="Yandex AI Conversation settings" src="images/conversation_settings.png" />
</p>

### 3. Text-to-Speech Settings (`Yandex AI TTS`)
Click the gear icon ⚙️ next to **Yandex AI TTS** to select the default voice, emotional role (`good`, `neutral`, `evil`), and speech speed (`0.1`–`3.0`, default `1.0`).

<p align="center">
  <img width="600" alt="Yandex AI TTS settings" src="images/tts_settings.png" />
</p>

#### Available Voices & Emotions (`ru-RU`):

| Voice | Voice ID | Gender | Supported Emotions |
| :--- | :--- | :--- | :--- |
| **Alena** | `alena` | Female | `neutral`, `good` |
| **Filipp** | `filipp` | Male | `neutral` |
| **Ermil** | `ermil` | Male | `neutral`, `good` |
| **Jane** | `jane` | Female | `neutral`, `good`, `evil` |
| **Omazh** | `omazh` | Female | `neutral`, `evil` |
| **Zahar** | `zahar` | Male | `neutral`, `good` |
| **Madirus** | `madirus` | Male | `neutral` |
| **Dasha / Julia / Lera / Masha / Marina** | `dasha`, `julia`, `lera`, `masha`, `marina` | Female | `neutral` (+ SpeechKit v3 roles) |
| **Alexander / Kirill / Anton** | `alexander`, `kirill`, `anton` | Male | `neutral` (+ SpeechKit v3 roles) |

*(Additional supported languages: `en-US` — `john`; `de-DE` — `lea`; `kk-KK` — `amira`, `madi`, `saule`, `zhanar`; `uz-UZ` — `nigora`, `lola`, `yulduz`; `he-IL` — `naomi`.)*

### 4. Setting Up **Assist** Voice Pipeline
1. Go to **Settings -> Voice Assistants** and create or edit an assistant.
2. Select **`Yandex AI Conversation`**, **`Yandex AI STT`**, and **`Yandex AI TTS`** (enable **"Prefer handling commands locally"** so simple commands run locally at 0 tokens).

<p align="center">
  <img width="600" alt="Assist pipeline configuration" src="images/assist_pipeline.png" />
</p>

<p align="center">
  <img width="500" alt="Example conversation in Assist" src="images/assist_chat.png" />
</p>

---

## 📊 Token & Estimated Cost Tracking (Beta)

Each of the 5 sub-services automatically provides persistent diagnostic sensors (`RestoreSensor`):
- **`Yandex AI Conversation` & `Yandex AI Task`**:
  - **Tokens Used (`tokens`)** — total tokens (sensor attributes expose `input_tokens`, `output_tokens`, `last_request_tokens`, `requests_count`, `last_model`).
  - **Cost (`RUB`)** — approximate cost in Russian rubles.
- **`Yandex AI Task image`**: **Images Generated (`img`)** and **Cost (`RUB`)**.
- **`Yandex AI TTS`**: **Characters Synthesized (`chars`)** and **Cost (`RUB`)**.
- **`Yandex AI STT`**: **Requests Recognized (`req`)** and **Cost (`RUB`)**.

> ⚠️ **Note:** RUB cost tracking operates in **Beta (informational) mode** and may differ from actual charges in Yandex Cloud Billing, as it uses public base unit rates and does not account for trial grants, custom discounts, billing rounding, or price-list updates.

---

## 🎨 Using AI Task (Image Generation, Structured Data & Camera Vision)

The integration provides two dedicated `ai_task` entities:
- **`Yandex AI Task`** (`ai_task.yandex_ai_task`) — text & structured JSON generation (`ai_task.generate_data`) via **YandexGPT**, plus multimodal camera/image analysis via **Gemma 3 27B Vision**.
- **`Yandex AI Task image`** (`ai_task.yandex_ai_task_image`) — image generation (`ai_task.generate_image`) via **Alice AI ART (`aliceai-image-art-3.0`)**.

### Example 1: Generate an Image with Alice AI ART (`ai_task.generate_image`)

```yaml
action: ai_task.generate_image
data:
  entity_id: ai_task.yandex_ai_task_image
  task_name: "Today's weather"
  instructions: "A cozy smart home in an autumn forest, warm glowing windows, cinematic lighting"
response_variable: generated_image
```

### Example 2: Generate Structured Data with YandexGPT (`ai_task.generate_data`)

```yaml
action: ai_task.generate_data
data:
  entity_id: ai_task.yandex_ai_task
  task_name: "Morning home summary"
  instructions: "Write a concise morning greeting summary based on the outdoor weather and bedroom temperature."
response_variable: summary
```

### Example 3: Camera & Image Vision Analysis (`ai_task.generate_data` + `attachments`)

`Yandex AI Task` supports `SUPPORT_ATTACHMENTS` and automatically analyzes attached camera snapshots or images using **`gemma-3-27b-it/latest`**:

```yaml
action: ai_task.generate_data
data:
  entity_id: ai_task.yandex_ai_task
  task_name: "Front door camera check"
  instructions: "Describe what is happening on the camera. Are there any people or vehicles?"
  attachments:
    - media_content_id: media-source://camera/camera.front_door
      media_content_type: image/jpeg
response_variable: camera_analysis
```

---

## 📂 Repository Structure

```text
HA-Yandex-generative_ai_conversation/
├── .github/workflows/          # GitHub Actions (Hassfest & HACS Validation, Release)
├── custom_components/
│   └── yandex_generative_ai_conversation/
│       ├── __init__.py         # Integration setup and Subentries lifecycle
│       ├── ai_task.py          # AI Task platform (YandexGPT + Vision + Alice AI ART)
│       ├── brand/              # Local brand icons and logos (icon.png, logo.png)
│       ├── config_flow.py      # Setup wizard and ConfigSubentryFlow
│       ├── const.py            # Constants, models, and voices/emotions
│       ├── conversation.py     # Conversation agent for Assist
│       ├── diagnostics.py      # Integration diagnostics with key redaction
│       ├── entity.py           # Base LLM client and ChatLog Tool Calling loop
│       ├── manifest.json       # Home Assistant integration manifest
│       ├── sensor.py           # Token, request, and estimated cost (RUB) sensors
│       ├── strings.json        # Localization strings
│       ├── stt.py              # Speech-to-Text (Yandex SpeechKit STT)
│       ├── tts.py              # Text-to-Speech (Yandex SpeechKit TTS v1 + v3)
│       └── translations/       # Translations (en.json, ru.json)
├── images/                     # Documentation screenshots
├── API_KEY_GUIDE.md            # Step-by-step guide to obtaining Folder ID & API Key
├── CHANGELOG.md                # Release history
├── LICENSE                     # MIT License
├── README.en.md                # English documentation
├── README.md                   # Russian documentation
└── hacs.json                   # HACS manifest
```

---

## 📄 License

This project is distributed under the **MIT License**. See [LICENSE](LICENSE) for details.


