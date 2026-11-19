<p align="center">
  <a href="README.md">🇷🇺 Русский</a> | <b>🇬🇧 English</b>
</p>

# 📂 Ready-to-Use Automation Examples

This directory contains ready-to-import automation examples tested on **Home Assistant 2025.8+ / 2026.x**. Open any `.yaml` file in `Raw` view and paste it into Home Assistant's Automation Editor (*"Edit in YAML"* mode).

## Example Files (English)

| File | Purpose |
| :--- | :--- |
| **[`en/vk_chatbot.yaml`](en/vk_chatbot.yaml)** | Smart chatbot for **VKontakte** (via [VK Notify](https://github.com/Eugen417/ha_vk_notify_plus)): natural 1-on-1 DM chat + **`Bot190` / `bot 190`** wake word in group chats. Supports text, voice messages (`transcript`), and photo attachments (`[image: <url>]`). |
| **[`en/vk_camera_vision.yaml`](en/vk_camera_vision.yaml)** | **`/camera`** command in VKontakte: captures a frame from `camera.*`, analyzes the scene via `Qwen3.6 35B Vision` (`ai_task.generate_data`), and replies with the snapshot and AI report. |
| **[`en/telegram_chatbot.yaml`](en/telegram_chatbot.yaml)** | Smart chatbot for **Telegram** (built-in `telegram_bot` integration, HA 2026+ schema): replies immediately in DMs (`chat_id > 0`) and on **`Bot190`** wake word in groups (`chat_id < 0`), supports text & photos (`telegram_bot.download_file`), `typing` indicator, and conversation memory. |
| **[`en/ai_task_examples.yaml`](en/ai_task_examples.yaml)** | Action snippets for `ai_task.generate_image` (*Alice AI ART 3.0*) and `ai_task.generate_data` (text summaries & *Qwen3.6 Vision* camera analysis). |

*(Russian versions of all YAML files are located directly in [`examples/`](README.md)).*

---

## ⚙️ 1-Minute Setup in Home Assistant's Visual Editor (UI Blocks)

All examples are structured so that after pasting into *"Edit in YAML"* and switching back to the **Visual Editor**, every trigger and action renders as **native Home Assistant UI cards** (no raw grey YAML blocks):

1. **In the `Event` trigger:** replace `peer_id: 2000000003` (for VK) or `user_id: [111222333, ...]` (for Telegram) with your own chat/user IDs.
2. **In `VK Notify` / `Telegram` actions:** select your chat entity (`notify.vk_notify_...` or `notify.telegram_bot_...`) from the dropdown menu.
3. **In `Conversation: Process`:** select your Yandex AI agent (for example, a dedicated `Yandex Chat Bot` subentry created via `+ Add conversation agent`).
4. *(For 1-on-1 VK Direct Messages)* — in the **Conditions ("And If")** section of `vk_chatbot.yaml`, you can disable the `bot 190` wake-word condition in one click so the bot replies to every message naturally!

---

## 🔍 Model & Conversation Agent Requirements for Vision & Reverse Image Search

In your Conversation Agent settings ⚙️, text Web Search and Reverse Image Search are **two independent toggles**:

1. **Required Yandex Cloud Role:** make sure your service account has the **`search-api.webSearch.user`** role (and the `yc.search-api.execute` scope if your API key uses restricted scopes — or generate an unrestricted key in 1 click at [aistudio.yandex.ru](https://aistudio.yandex.ru/)).
2. **Model Requirements for Reverse Image Search (`image_search`):**
   - Reverse Image Search requires a multimodal model that supports **both image inputs (`Vision`) and Function Calling (`tools`)**.
   - **Recommended model:** **`Qwen3.6 35B Vision` (`qwen3.6-35b-a3b/latest`)** (or `deepseek-v4.1-flash/latest`).
   - **Automatic Vision Fallback:** if you keep **"Recommended model settings" = On** (`yandexgpt-5.1/latest`) or use a text model (`aliceai-llm-flash/latest`, `aliceai-llm/latest`), the integration **automatically switches** image-containing turns to **`qwen3.6-35b-a3b/latest`**!
   - ⚠️ **Do NOT select legacy `Gemma 3 27B Vision` (`gemma-3-27b-it/latest`)** when Web Search, Reverse Image Search, or `AI tools` are enabled — `Gemma 3` does not support Function Calling (`tools`) in Yandex AI Studio.
3. **Privacy & Cost Control for Photos:**
   - **Local AI Vision only (`Reverse Image Search = Off`, default):** attached photos (utility meters, receipts, documents, error screens) are read **only** by `Qwen3.6 35B Vision` — `yandex_image_search` is disabled (`0 RUB` search fee).
   - **Yandex Smart Camera mode (`Reverse Image Search = On`):** enables `POST /v2/image/search_by_image` (CBIR, `0.915 RUB` when invoked) so the model can identify exact plant species, products, spare parts, or landmarks and return matching web/store links.
   - To disable photo handling completely in an automation, remove the `photo_tags` variable in `vk_chatbot.yaml` (or the `telegram_attachment` trigger in `telegram_chatbot.yaml`), or restrict `yandex_image_search` to a specific domain in your system prompt (e.g., `site: "wikipedia.org"`).
