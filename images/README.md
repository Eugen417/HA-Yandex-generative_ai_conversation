# Скриншоты для документации (README.md и API_KEY_GUIDE.md)

Положите ваши скриншоты в эту папку (`images/`) со следующими именами (или переименуйте ссылки в `README.md` / `API_KEY_GUIDE.md`):

### Для `README.md`:
- `services_overview.png` — общий вид интеграции **Yandex AI Studio** со списком всех 4 служб (`Conversation`, `STT`, `TTS`, `AI Task`) и кнопками `+ Добавить...`
- `conversation_settings.png` — окно настроек диалоговой системы (`Yandex AI Conversation`: промпт, управление Home Assistant, модель, температура)
- `tts_settings.png` — окно настроек синтеза речи (`Yandex AI TTS`: голос, эмоция, скорость)
- `assist_pipeline.png` — окно настройки голосового ассистента (**Assist**) с выбранными `Yandex AI Conversation`, `Yandex AI STT` и `Yandex AI TTS` (выбор языка и голоса)
- `assist_chat.png` — пример диалога с ассистентом (управление светом / запрос температуры в комнате)

### Для `API_KEY_GUIDE.md`:
- `yc_folder_id.png` — где найти **Folder ID** (идентификатор каталога) в Yandex Cloud / Yandex AI Studio
- `yc_service_account.png` — создание сервисного аккаунта и назначение ролей (`ai.languageModels.user`, `ai.imageGeneration.user`, `ai.speechkit-stt.user`, `ai.speechkit-tts.user`)
- `yc_api_key.png` — создание и копирование **API-ключа** (`Api-Key`)
