"""Config flow for Yandex AI Studio integration."""

from collections.abc import Mapping
from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_NAME, CONF_PROMPT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CHAT_MODELS,
    CONF_CHAT_MODEL,
    CONF_FOLDER_ID,
    CONF_IMAGE_MODEL,
    CONF_MAX_TOKENS,
    CONF_RECOMMENDED,
    CONF_STT_LANGUAGE,
    CONF_STT_MODEL,
    CONF_TEMPERATURE,
    CONF_TTS_EMOTION,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_AI_TASK_IMAGE_NAME,
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CHAT_MODEL,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_STT_LANGUAGE,
    DEFAULT_STT_MODEL,
    DEFAULT_STT_NAME,
    DEFAULT_TITLE,
    DEFAULT_TTS_EMOTION,
    DEFAULT_TTS_NAME,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    DOMAIN,
    IMAGE_MODELS,
    RECOMMENDED_AI_TASK_IMAGE_OPTIONS,
    RECOMMENDED_AI_TASK_OPTIONS,
    RECOMMENDED_CONVERSATION_OPTIONS,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_STT_OPTIONS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TTS_OPTIONS,
    STT_LANGUAGES,
    STT_MODELS,
)


class YandexAIConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yandex AI Studio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            name = user_input.pop("name", DEFAULT_TITLE)
            return self.async_create_entry(
                title=name,
                data=user_input,
                subentries=[
                    {
                        "subentry_type": "conversation",
                        "data": RECOMMENDED_CONVERSATION_OPTIONS,
                        "title": DEFAULT_CONVERSATION_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "tts",
                        "data": RECOMMENDED_TTS_OPTIONS,
                        "title": DEFAULT_TTS_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "ai_task_data",
                        "data": RECOMMENDED_AI_TASK_OPTIONS,
                        "title": DEFAULT_AI_TASK_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "ai_task_image",
                        "data": RECOMMENDED_AI_TASK_IMAGE_OPTIONS,
                        "title": DEFAULT_AI_TASK_IMAGE_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "stt",
                        "data": RECOMMENDED_STT_OPTIONS,
                        "title": DEFAULT_STT_NAME,
                        "unique_id": None,
                    },
                ],
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=DEFAULT_TITLE): TextSelector(),
                    vol.Required(CONF_FOLDER_ID): TextSelector(),
                    vol.Required(CONF_API_KEY): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
        )

    @classmethod
    @callback
    @override
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {
            "conversation": YandexAISubentryFlowHandler,
            "stt": YandexAISubentryFlowHandler,
            "tts": YandexAISubentryFlowHandler,
            "ai_task_data": YandexAISubentryFlowHandler,
            "ai_task_image": YandexAISubentryFlowHandler,
        }




class YandexAISubentryFlowHandler(ConfigSubentryFlow):
    """Flow for managing Yandex AI Studio subentries."""

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == "user"

    async def async_step_set_options(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Set subentry options."""
        if self._get_entry().state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is None:
            if self._is_new:
                if self._subentry_type == "tts":
                    options = RECOMMENDED_TTS_OPTIONS.copy()
                elif self._subentry_type == "stt":
                    options = RECOMMENDED_STT_OPTIONS.copy()
                elif self._subentry_type == "ai_task_data":
                    options = RECOMMENDED_AI_TASK_OPTIONS.copy()
                elif self._subentry_type == "ai_task_image":
                    options = RECOMMENDED_AI_TASK_IMAGE_OPTIONS.copy()
                else:
                    options = RECOMMENDED_CONVERSATION_OPTIONS.copy()
            else:
                options = self._get_reconfigure_subentry().data.copy()
        else:
            if user_input.get(CONF_LLM_HASS_API) is None:
                user_input.pop(CONF_LLM_HASS_API, None)

            if self._is_new:
                return self.async_create_entry(
                    title=user_input.pop(CONF_NAME),
                    data=user_input,
                )

            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data=user_input,
            )

        schema = _yandex_config_option_schema(
            self.hass, self._is_new, self._subentry_type, options
        )
        return self.async_show_form(
            step_id="set_options",
            data_schema=vol.Schema(schema),
        )

    async_step_reconfigure = async_step_set_options
    async_step_user = async_step_set_options


def _yandex_config_option_schema(
    hass: HomeAssistant,
    is_new: bool,
    subentry_type: str,
    options: Mapping[str, Any],
) -> dict[Any, Any]:
    """Return a schema for Yandex AI Studio subentry options."""
    if is_new:
        if subentry_type == "tts":
            default_name = DEFAULT_TTS_NAME
        elif subentry_type == "stt":
            default_name = DEFAULT_STT_NAME
        elif subentry_type == "ai_task_data":
            default_name = DEFAULT_AI_TASK_NAME
        elif subentry_type == "ai_task_image":
            default_name = DEFAULT_AI_TASK_IMAGE_NAME
        else:
            default_name = DEFAULT_CONVERSATION_NAME
        schema: dict[Any, Any] = {
            vol.Required(CONF_NAME, default=default_name): str,
        }
    else:
        schema = {}

    chat_model_choices = [SelectOptionDict(label=m, value=m) for m in CHAT_MODELS]
    image_model_choices = [SelectOptionDict(label=m, value=m) for m in IMAGE_MODELS]

    if subentry_type == "conversation":
        hass_apis = [
            SelectOptionDict(label=api.name, value=api.id)
            for api in llm.async_get_apis(hass)
        ]
        suggested_apis = options.get(CONF_LLM_HASS_API, [llm.LLM_API_ASSIST])
        if isinstance(suggested_apis, str):
            suggested_apis = [suggested_apis] if suggested_apis != "none" else []
        elif not isinstance(suggested_apis, list):
            suggested_apis = []
        known_apis = {api.id for api in llm.async_get_apis(hass)}
        suggested_apis = [a for a in suggested_apis if a in known_apis]

        schema.update(
            {
                vol.Optional(
                    CONF_PROMPT,
                    description={
                        "suggested_value": options.get(CONF_PROMPT, DEFAULT_PROMPT)
                    },
                    default=options.get(CONF_PROMPT, DEFAULT_PROMPT),
                ): TemplateSelector(),
                vol.Optional(
                    CONF_LLM_HASS_API,
                    description={"suggested_value": suggested_apis},
                    default=suggested_apis,
                ): SelectSelector(
                    SelectSelectorConfig(options=hass_apis, multiple=True)
                ),
                vol.Optional(
                    CONF_RECOMMENDED,
                    default=options.get(CONF_RECOMMENDED, True),
                ): BooleanSelector(),
                vol.Optional(
                    CONF_CHAT_MODEL,
                    default=options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=chat_model_choices,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=1.0, step=0.05, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=100, max=8000, step=100, mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )

    elif subentry_type == "stt":
        stt_model_choices = [SelectOptionDict(label=m, value=m) for m in STT_MODELS]
        stt_lang_choices = [
            SelectOptionDict(label=lang, value=lang) for lang in STT_LANGUAGES
        ]
        schema.update(
            {
                vol.Optional(
                    CONF_STT_MODEL,
                    default=options.get(CONF_STT_MODEL, DEFAULT_STT_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=stt_model_choices,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(
                    CONF_STT_LANGUAGE,
                    default=options.get(CONF_STT_LANGUAGE, DEFAULT_STT_LANGUAGE),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=stt_lang_choices,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
    elif subentry_type == "tts":
        voice_choices = [
            SelectOptionDict(label="Алёна (Женский)", value="alena"),
            SelectOptionDict(label="Филипп (Мужской)", value="filipp"),
            SelectOptionDict(label="Эрмил (Мужской)", value="ermil"),
            SelectOptionDict(label="Джейн (Женский)", value="jane"),
            SelectOptionDict(label="Мадирус (Мужской)", value="madirus"),
            SelectOptionDict(label="Омаж (Женский)", value="omazh"),
            SelectOptionDict(label="Захар (Мужской)", value="zahar"),
            SelectOptionDict(label="Даша (Женский)", value="dasha"),
            SelectOptionDict(label="Юлия (Женский)", value="julia"),
            SelectOptionDict(label="Лера (Женский)", value="lera"),
            SelectOptionDict(label="Маша (Женский)", value="masha"),
            SelectOptionDict(label="Марина (Женский)", value="marina"),
            SelectOptionDict(label="Александр (Мужской)", value="alexander"),
            SelectOptionDict(label="Кирилл (Мужской)", value="kirill"),
            SelectOptionDict(label="Антон (Мужской)", value="anton"),
            SelectOptionDict(label="John (en-US)", value="john"),
            SelectOptionDict(label="Lea (de-DE)", value="lea"),
            SelectOptionDict(label="Amira (kk-KK)", value="amira"),
            SelectOptionDict(label="Madi (kk-KK)", value="madi"),
            SelectOptionDict(label="Nigora (uz-UZ)", value="nigora"),
            SelectOptionDict(label="Naomi (he-IL)", value="naomi"),
        ]
        emotion_choices = [
            SelectOptionDict(label="Радостный (good)", value="good"),
            SelectOptionDict(label="Нейтральный (neutral)", value="neutral"),
            SelectOptionDict(label="Раздраженный (evil)", value="evil"),
        ]
        schema.update(
            {
                vol.Optional(
                    CONF_TTS_VOICE,
                    default=options.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=voice_choices, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    CONF_TTS_EMOTION,
                    default=options.get(CONF_TTS_EMOTION, DEFAULT_TTS_EMOTION),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=emotion_choices, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    CONF_TTS_SPEED,
                    default=options.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1, max=3.0, step=0.1, mode=NumberSelectorMode.SLIDER
                    )
                ),
            }
        )
    elif subentry_type == "ai_task_data":
        schema.update(
            {
                vol.Optional(
                    CONF_RECOMMENDED,
                    default=options.get(CONF_RECOMMENDED, True),
                ): BooleanSelector(),
                vol.Optional(
                    CONF_CHAT_MODEL,
                    default=options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=chat_model_choices,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=1.0, step=0.05, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=100, max=8000, step=100, mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )
    elif subentry_type == "ai_task_image":
        schema.update(
            {
                vol.Optional(
                    CONF_IMAGE_MODEL,
                    default=options.get(CONF_IMAGE_MODEL, DEFAULT_IMAGE_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=image_model_choices,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
            }
        )

    return schema

