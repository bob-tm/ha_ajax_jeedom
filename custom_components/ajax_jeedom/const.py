"""Constants for openHAB."""
from datetime import timedelta
from logging import Logger, getLogger

# Base component constants
NAME = "Jeedom Ajax Bridge"
DOMAIN = "ajax_jeedom"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
LOGGER: Logger = getLogger(__package__)

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
PLATFORMS = [SENSOR, BINARY_SENSOR, 'button']

BinarySensors = ['online', 'reedClosed', 'realState', 'extraContactClosed', 'tampered', 'ethernet::enabled', 'externallyPowered', 'gsm::gprsEnabled', 'gsmNetworkStatus' ]
Diagnostic    = ['event', 'eventCode', 'signalLevel', 'sourceObjectName', 'online', 'gsmNetworkStatus', 'gsm::signalLevel', 'gsm::gprsEnabled', 'gsm::networkStatus', 'ethernet::enabled', 'buzzerState']

# Configuration and options
CONF_BASE_URL = "base_url"
CONF_AUTH_TOKEN = "auth_token"
CONF_PANIC_BUTTON = "panic_button"


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
-------------------------------------------------------------------
"""
