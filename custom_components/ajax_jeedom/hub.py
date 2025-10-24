"""A demonstration 'hub' that connects several devices."""
from __future__ import annotations

# In a real implementation, this would be in an external library that's on PyPI.
# The PyPI package needs to be included in the `requirements` section of manifest.json
# See https://developers.home-assistant.io/docs/creating_integration_manifest
# for more information.
# This dummy hub always returns 3 rollers.
import asyncio
import os
import json

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from .const import CONF_AUTH_TOKEN, CONF_BASE_URL, CONF_PANIC_BUTTON

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage

from homeassistant.components.sensor import (
    SensorDeviceClass
)

from homeassistant.helpers.storage import STORAGE_DIR
from .api import Jeedom
from .const import DOMAIN, LOGGER, PLATFORMS
from .utils import strip_ip

async def ConfigFlowTestConnection(host, token):
    try:
        jeedom = Jeedom(host.rstrip('\\'), token)
        r = await jeedom.isOk()
        if r==True:
            return True
        else:
            return False

    except:
        return False

class AjaxHub:
    manufacturer = "Ajax"
    disk_cache   = False

    def __init__(self, hass: HomeAssistant, entry_data, config_entry) -> None:
        """Init dummy hub."""
        self._apikey = entry_data[CONF_AUTH_TOKEN]
        self._host   = entry_data[CONF_BASE_URL].rstrip('\\')
        self._enable_panic_button = entry_data[CONF_PANIC_BUTTON]
        self._hass   = hass
        self._name   = self._host
        self._id     = self._host.lower()
        self.devices = {}
        self.jdindex = {}
        self.config_entry = config_entry
        self.online = True
        if self.disk_cache:
            self.cache_folder = hass.config.path(STORAGE_DIR, 'ajax_jeedom')
            os.makedirs(self.cache_folder, exist_ok=True)
            self.cache_folder = self.cache_folder + os.sep + strip_ip(self._host.lower())
            os.makedirs(self.cache_folder, exist_ok=True)

    def getCachedJsonFile(self, id):
        if not self.disk_cache:
            return False

        fn = self.cache_folder + os.sep + str(id) + '.json'
        if not os.path.exists(fn):
            return False

        with open(fn) as json_data:
            return json.load(json_data)

    def saveJsonToCache(self, id, data):
        if not self.disk_cache:
            return False

        fn = self.cache_folder + os.sep + str(id) + '.json'
        json_str = json.dumps(data, indent=4)
        with open(fn, "w") as f:
            f.write(json_str)

    async def GetAjaxJson(self):
        self.jeedom = Jeedom(self._host, self._apikey)
        self.ajax   = self.getCachedJsonFile('all')

        if self.ajax == False:
            self.ajax   = await self.jeedom.eqLogic.byType(type='ajaxSystem')
            self.saveJsonToCache('all', self.ajax)

        for d in self.ajax:
            jd_id = d['id']
            details_json = self.getCachedJsonFile(jd_id)
            if details_json == False:
                details_json = await self.jeedom.eqLogic.fullById(id=jd_id)
                self.saveJsonToCache(jd_id, details_json)

            self.create_device(d, details_json)


        await self._hass.config_entries.async_forward_entry_setups(self.config_entry, PLATFORMS)

    async def Subscribe(self, hass):
        @callback
        async def message_received(msg):
            await self.parse_mqtt_message(msg.topic, msg.payload)

        await mqtt.async_subscribe(hass, "jeedom/#", message_received)

    def create_device(self, d, details):
        device_registry = dr.async_get(self._hass)

        t  = d['configuration']['type']

        if t != 'group':
            fw = d['configuration']['firmware']
        else:
            fw = ''

        device = device_registry.async_get_or_create(
                    config_entry_id = self.config_entry.entry_id,
                    connections     = {(d['logicalId'], DOMAIN)},
                    identifiers     = {(d['logicalId'], DOMAIN)},
                    manufacturer    = self.manufacturer,
                    name            = d['name'],
                    model           = d['configuration']['device'],
                    serial_number   = d['logicalId'],
                    sw_version      = fw,
                    hw_version      = f"Jeedom id: {d['id']}",
                )

        #print(d['id'], d['name'], d['configuration']['device'])
        #for c in details['cmds']:
        #    print(c['id'], c['type'], c['logicalId'],  c['currentValue'])

            #if c['generic_type']:
            #    print(c['generic_type'])

        #print("\n")

        ad = AjaxDevice(self, device, d, details)
        self.devices[d['logicalId']]=ad

        for c in details['cmds']:
            self.jdindex[c['id']]=(ad, c['currentValue'], set())

        return ad


    async def parse_mqtt_message(self, topic, payload):
        # jeedom/cmd/event/576
        # jeedom/state online
        if topic.startswith("jeedom/cmd/event/"):
            x = topic.split('/')
            try:
                id = int(x[len(x)-1])

                p = json.loads(payload)
                print(id, p['value'])

                L = list(self.jdindex[id])
                L[1] = p['value']
                self.jdindex[id]=tuple(L)

                await L[0].update_value_from_mqtt_message(id, p)
            except:
                LOGGER.error(f"Exception in parse_mqtt_message: topic {topic} and payload {payload}")
        else:
            LOGGER.info(f"parse_mqtt_message: unsupported topic {topic} and payload {payload}")


    @property
    def hub_id(self) -> str:
        """ID for dummy hub."""
        print(f"hub_id {self._id}")
        return self._id

    async def test_connection(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""
        await asyncio.sleep(1)
        print("test_connection")

        return True


class AjaxDevice:
    details = False

    def __init__(self, hub: AjaxHub, device_registry, device_json, details_json) -> None:
        self.logicalId  = device_json['logicalId']
        self.json       = device_json
        self.details    = details_json
        self.hub        = hub
        self._callbacks = set()

    async def update_value_from_mqtt_message(self, id, payload):
        await self.publish_updates(id)

    def value_by_jd_id(self, id):
        return self.hub.jdindex[id][1] # self.details['cmds']

    def register_callback(self, id, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state."""
        self.hub.jdindex[id][2].add(callback)

    def remove_callback(self, id, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self.hub.jdindex[id][2].discard(callback)


    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self, id) -> None:
        """Schedule call all registered callbacks."""
        for callback in self.hub.jdindex[id][2]:
            callback()


    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def exec_command(self, id, cmd_name) -> None:
        if (not self.hub._enable_panic_button) and (cmd_name=='PANIC'):
            raise ServiceValidationError('Panic button is Disabled')
        else:
            r = await self.hub.jeedom.cmd.execCmd(id)
            if 'error' in r:
                raise ServiceValidationError(r['error']['message'])

            return r


    @property
    def online(self) -> bool:
        return True

    @property
    def battery_level(self) -> int:
        if self.json:
            return 34
            #return self.json['sensor']['battery']
