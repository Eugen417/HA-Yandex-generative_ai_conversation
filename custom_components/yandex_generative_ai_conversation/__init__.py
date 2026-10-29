"""The Yandex AI Studio integration."""

import logging
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
    llm,
)

from .const import (
    CONF_CHAT_MODEL,
    CONF_LLM_HASS_API,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
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
    DEFAULT_STT_NAME,
    DEFAULT_TTS_EMOTION,
    DEFAULT_TTS_NAME,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    DOMAIN,
    PLATFORMS,
    RECOMMENDED_AI_TASK_IMAGE_OPTIONS,
    RECOMMENDED_AI_TASK_OPTIONS,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_STT_OPTIONS,
    RECOMMENDED_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Yandex AI Studio from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Clean up legacy shared hub device so each subentry owns its own service device
    device_registry = dr.async_get(hass)
    if legacy_device := device_registry.async_get_device(
        identifiers={(DOMAIN, entry.entry_id)}
    ):
        device_registry.async_remove_device(legacy_device.id)

    entity_registry = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if ent.config_subentry_id is None or ent.config_subentry_id not in entry.subentries:
            entity_registry.async_remove(ent.entity_id)

    existing_types = {sub.subentry_type for sub in entry.subentries.values()}

    if "conversation" not in existing_types:
        raw_api = entry.options.get(CONF_LLM_HASS_API, [llm.LLM_API_ASSIST])
        if isinstance(raw_api, str):
            llm_apis = [raw_api] if raw_api != "none" else [llm.LLM_API_ASSIST]
        elif isinstance(raw_api, list) and raw_api and raw_api != ["none"]:
            llm_apis = raw_api
        else:
            llm_apis = [llm.LLM_API_ASSIST]

        conv_opts = {
            CONF_LLM_HASS_API: llm_apis,
            CONF_CHAT_MODEL: entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL),
            CONF_PROMPT: entry.options.get(CONF_PROMPT, DEFAULT_PROMPT),
            CONF_TEMPERATURE: entry.options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
            CONF_MAX_TOKENS: entry.options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
        }
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(conv_opts),
                subentry_type="conversation",
                title=DEFAULT_CONVERSATION_NAME,
                unique_id=None,
            ),
        )
    else:
        for sub in list(entry.subentries.values()):
            if sub.subentry_type == "conversation":
                api_val = sub.data.get(CONF_LLM_HASS_API)
                if api_val in (None, [], "none", ["none"]):
                    new_data = dict(sub.data)
                    new_data[CONF_LLM_HASS_API] = [llm.LLM_API_ASSIST]
                    hass.config_entries.async_update_subentry(entry, sub, data=new_data)

    if "stt" not in existing_types:
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(RECOMMENDED_STT_OPTIONS),
                subentry_type="stt",
                title=DEFAULT_STT_NAME,
                unique_id=None,
            ),
        )
    else:
        for sub in list(entry.subentries.values()):
            if sub.subentry_type == "stt" and not sub.data:
                hass.config_entries.async_update_subentry(
                    entry, sub, data=dict(RECOMMENDED_STT_OPTIONS)
                )

    if "tts" not in existing_types:
        tts_opts = {
            CONF_TTS_VOICE: entry.options.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE),
            CONF_TTS_EMOTION: entry.options.get(CONF_TTS_EMOTION, DEFAULT_TTS_EMOTION),
            CONF_TTS_SPEED: entry.options.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED),
        }
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(tts_opts),
                subentry_type="tts",
                title=DEFAULT_TTS_NAME,
                unique_id=None,
            ),
        )

    if "ai_task_data" not in existing_types:
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(RECOMMENDED_AI_TASK_OPTIONS),
                subentry_type="ai_task_data",
                title=DEFAULT_AI_TASK_NAME,
                unique_id=None,
            ),
        )
    else:
        for sub in list(entry.subentries.values()):
            if sub.subentry_type == "ai_task_data" and not sub.data:
                hass.config_entries.async_update_subentry(
                    entry, sub, data=dict(RECOMMENDED_AI_TASK_OPTIONS)
                )

    if "ai_task_image" not in existing_types:
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(RECOMMENDED_AI_TASK_IMAGE_OPTIONS),
                subentry_type="ai_task_image",
                title=DEFAULT_AI_TASK_IMAGE_NAME,
                unique_id=None,
            ),
        )
    else:
        for sub in list(entry.subentries.values()):
            if sub.subentry_type == "ai_task_image":
                if not sub.data or str(sub.data.get("image_model", "")).startswith(
                    "yandex-art"
                ):
                    hass.config_entries.async_update_subentry(
                        entry,
                        sub,
                        data=dict(RECOMMENDED_AI_TASK_IMAGE_OPTIONS),
                    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

