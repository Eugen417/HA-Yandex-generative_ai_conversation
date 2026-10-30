"""Sensor platform for Yandex AI Studio usage and cost tracking."""

from __future__ import annotations

from typing import Any, override

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_CHAT_MODEL,
    CONF_IMAGE_MODEL,
    CONF_RECOMMENDED,
    CONF_STT_MODEL,
    CONF_TTS_VOICE,
    DEFAULT_CHAT_MODEL,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_VOICE,
    DOMAIN,
)


def _subentry_default_model(subentry: ConfigSubentry) -> str:
    """Return the display model for a subentry device."""
    if subentry.subentry_type == "ai_task_image":
        if subentry.data.get(CONF_RECOMMENDED):
            return DEFAULT_IMAGE_MODEL
        return str(subentry.data.get(CONF_IMAGE_MODEL) or DEFAULT_IMAGE_MODEL)
    if subentry.subentry_type == "stt":
        return str(subentry.data.get(CONF_STT_MODEL) or DEFAULT_STT_MODEL)
    if subentry.subentry_type == "tts":
        return str(subentry.data.get(CONF_TTS_VOICE) or DEFAULT_TTS_VOICE)
    if subentry.data.get(CONF_RECOMMENDED):
        return DEFAULT_CHAT_MODEL
    return str(subentry.data.get(CONF_CHAT_MODEL) or DEFAULT_CHAT_MODEL)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Yandex AI Studio usage and cost sensors for each subentry."""
    for subentry in config_entry.subentries.values():
        entities: list[RestoreSensor] = [
            YandexSubentryUsageSensor(config_entry, subentry),
            YandexSubentryCostSensor(config_entry, subentry),
        ]
        async_add_entities(
            entities,
            config_subentry_id=subentry.subentry_id,
        )


class YandexSubentryUsageSensor(RestoreSensor):
    """Sensor tracking tokens, images, TTS characters, or STT requests."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the usage sensor."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = f"{subentry.subentry_id}_usage"
        self._attr_native_value: int = 0
        self._extra_attrs: dict[str, Any] = {"requests_count": 0}

        stype = subentry.subentry_type
        if stype in ("conversation", "ai_task_data"):
            self._attr_name = "Потрачено токенов"
            self._attr_native_unit_of_measurement = "tokens"
            self._attr_icon = "mdi:counter"
            self._extra_attrs.update(
                {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "last_request_tokens": 0,
                }
            )
        elif stype == "ai_task_image":
            self._attr_name = "Сгенерировано изображений"
            self._attr_native_unit_of_measurement = "img"
            self._attr_icon = "mdi:image-multiple"
        elif stype == "tts":
            self._attr_name = "Озвучено символов"
            self._attr_native_unit_of_measurement = "chars"
            self._attr_icon = "mdi:script-text-outline"
        else:
            self._attr_name = "Распознано запросов"
            self._attr_native_unit_of_measurement = "req"
            self._attr_icon = "mdi:microphone-message"

        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Yandex",
            model=_subentry_default_model(subentry),
            entry_type=dr.DeviceEntryType.SERVICE,
        )


    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return self._extra_attrs

    @override
    async def async_added_to_hass(self) -> None:
        """Restore previous state and subscribe to usage events."""
        await super().async_added_to_hass()
        if (last_sensor := await self.async_get_last_sensor_data()) is not None:
            try:
                if last_sensor.native_value is not None:
                    self._attr_native_value = int(float(str(last_sensor.native_value)))
            except (TypeError, ValueError):
                self._attr_native_value = 0

        if (last_state := await self.async_get_last_state()) is not None:
            for key in (
                "requests_count",
                "input_tokens",
                "output_tokens",
                "last_request_tokens",
                "last_model",
            ):
                if key in last_state.attributes:
                    self._extra_attrs[key] = last_state.attributes[key]

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                self._handle_usage_event,
            )
        )

    @callback
    def _handle_usage_event(self, data: dict[str, Any]) -> None:
        """Update usage counters when a request finishes."""
        increment = int(
            data.get("tokens")
            or data.get("images")
            or data.get("chars")
            or data.get("requests")
            or 0
        )
        self._attr_native_value = int(self._attr_native_value or 0) + increment
        self._extra_attrs["requests_count"] = (
            int(self._extra_attrs.get("requests_count", 0)) + 1
        )
        if "input_tokens" in data:
            self._extra_attrs["input_tokens"] = int(
                self._extra_attrs.get("input_tokens", 0)
            ) + int(data["input_tokens"])
            self._extra_attrs["output_tokens"] = int(
                self._extra_attrs.get("output_tokens", 0)
            ) + int(data.get("output_tokens", 0))
            self._extra_attrs["last_request_tokens"] = int(data.get("tokens", 0))
        if "model" in data:
            self._extra_attrs["last_model"] = data["model"]

        self.async_write_ha_state()


class YandexSubentryCostSensor(RestoreSensor):
    """Sensor tracking estimated cost in RUB for a subentry."""

    _attr_has_entity_name = True
    _attr_name = "Затраты"
    _attr_native_unit_of_measurement = "RUB"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:currency-rub"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the cost sensor."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = f"{subentry.subentry_id}_cost_rub"
        self._attr_native_value: float = 0.0
        self._extra_attrs: dict[str, Any] = {
            "requests_count": 0,
            "last_request_cost_rub": 0.0,
        }
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Yandex",
            model=_subentry_default_model(subentry),
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return self._extra_attrs

    @override
    async def async_added_to_hass(self) -> None:
        """Restore previous state and subscribe to usage events."""
        await super().async_added_to_hass()
        if (last_sensor := await self.async_get_last_sensor_data()) is not None:
            try:
                if last_sensor.native_value is not None:
                    self._attr_native_value = round(
                        float(str(last_sensor.native_value)), 4
                    )
            except (TypeError, ValueError):
                self._attr_native_value = 0.0

        if (last_state := await self.async_get_last_state()) is not None:
            for key in ("requests_count", "last_request_cost_rub", "last_model"):
                if key in last_state.attributes:
                    self._extra_attrs[key] = last_state.attributes[key]

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_usage_{self.subentry.subentry_id}",
                self._handle_usage_event,
            )
        )

    @callback
    def _handle_usage_event(self, data: dict[str, Any]) -> None:
        """Update cost when a request finishes."""
        cost_delta = float(data.get("cost_rub", 0.0))
        self._attr_native_value = round(
            float(self._attr_native_value or 0.0) + cost_delta, 4
        )
        self._extra_attrs["requests_count"] = (
            int(self._extra_attrs.get("requests_count", 0)) + 1
        )
        self._extra_attrs["last_request_cost_rub"] = round(cost_delta, 4)
        if "model" in data:
            self._extra_attrs["last_model"] = data["model"]

        self.async_write_ha_state()
