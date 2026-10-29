"""Conversation support for the Yandex AI Studio integration."""

from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEFAULT_CHAT_MODEL, DOMAIN
from .entity import YandexAIBaseLLMEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "conversation":
            continue

        async_add_entities(
            [YandexAIConversationEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class YandexAIConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
    YandexAIBaseLLMEntity,
):
    """Yandex AI Studio conversation agent."""

    _attr_supports_streaming = True

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the agent."""
        super().__init__(entry, subentry, DEFAULT_CHAT_MODEL)
        llm_hass_api = self.subentry.data.get(CONF_LLM_HASS_API)
        if llm_hass_api and llm_hass_api != "none" and llm_hass_api != ["none"]:
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Call the API."""
        options = self.subentry.data
        raw_apis = options.get(CONF_LLM_HASS_API)
        llm_apis: list[str] | str | None = None
        if isinstance(raw_apis, list):
            filtered = [a for a in raw_apis if a and a != "none"]
            llm_apis = filtered or None
        elif isinstance(raw_apis, str) and raw_apis != "none":
            llm_apis = raw_apis

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                llm_apis,
                options.get(CONF_PROMPT),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        await self._async_handle_chat_log(chat_log)

        return conversation.async_get_result_from_chat_log(user_input, chat_log)

