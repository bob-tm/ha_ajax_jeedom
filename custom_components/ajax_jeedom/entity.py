
from homeassistant.components.sensor import (SensorDeviceClass)
from homeassistant.components.binary_sensor import (BinarySensorDeviceClass)

from homeassistant.const import (
    EntityCategory,
    UnitOfTemperature
)

from homeassistant.helpers.entity import Entity
from homeassistant.components.button import ButtonEntity
from homeassistant.util.unit_system import TEMPERATURE_UNITS

from .const import DOMAIN, LOGGER, BinarySensors, Diagnostic

def get_list_of_sensors(platform, hub):
    sensors = []

    if platform=='button':
        for logicid, ad in hub.devices.items():
            for c in ad.details['cmds']:
                if c['type']=='action':
                    sensors.append(ButtonBase(ad, c, platform))
    else:
        for logicid, ad in hub.devices.items():
            for c in ad.details['cmds']:
                if c['type']=='info':
                    if c['logicalId'] in BinarySensors:
                        if platform=='binary_sensor':
                            sensors.append(SensorBase(ad, c, platform))
                    else:
                        if platform=='sensor':
                            sensors.append(SensorBase(ad, c, platform))

    return sensors


class SensorBase(Entity):
    _attr_should_poll  = False

    def __init__(self, ad, json, platform):
        """Initialize the sensor."""
        self._ad        = ad
        self._jd_id     = json['id']
        self._is_binary = platform=='binary_sensor'
        self._logicalId = json['logicalId']

        self._attr_unique_id    = f"{self._ad.logicalId}_{self._jd_id}"
        self._attr_name         = json['logicalId'] #+'_'+str(json['id'])
        self.entity_id          = f"{platform}.{self._ad.logicalId}_{json['logicalId']}"

        if self._logicalId == 'temperature':
            self._attr_device_class        = SensorDeviceClass.TEMPERATURE;
            self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS;
        elif self._logicalId == 'voltage':
            self._attr_device_class        = SensorDeviceClass.VOLTAGE;
            self._attr_unit_of_measurement = 'V'
        elif self._logicalId == 'currentMA':
            self._attr_device_class        = SensorDeviceClass.CURRENT;
            self._attr_unit_of_measurement = 'mA'
        elif self._logicalId == 'powerWtH':
            self._attr_device_class        = SensorDeviceClass.ENERGY;
            self._attr_unit_of_measurement = 'Wh'
        elif self._logicalId == 'voltage':
            self._attr_device_class        = SensorDeviceClass.VOLTAGE;
            self._attr_unit_of_measurement = 'V'
        elif self._logicalId in ['reedClosed', 'extraContactClosed']:
            self._attr_device_class        = BinarySensorDeviceClass.WINDOW
        elif self._logicalId in ['tampered']:
            self._attr_device_class        = BinarySensorDeviceClass.TAMPER


    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(self._ad.logicalId, DOMAIN)}}

    @property
    def entity_category(self):
        if self._logicalId in Diagnostic:
            return EntityCategory.DIAGNOSTIC
        else:
            return None

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._ad.online

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._ad.register_callback(self._jd_id, self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._ad.remove_callback(self._jd_id, self.async_write_ha_state)


    @property
    def state(self):
        x = self._ad.value_by_jd_id(self._jd_id)
        if self._is_binary:
            x = int(x)==1
        return x




class ButtonBase(SensorBase, ButtonEntity):
    async def async_press(self):
        result = await self._ad.exec_command(self._jd_id, self._logicalId)
        print(result)