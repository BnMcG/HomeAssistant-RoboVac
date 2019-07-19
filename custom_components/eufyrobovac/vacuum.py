"""Support Eufy RoboVac devices."""
import logging
import async_timeout
import voluptuous as vol
import asyncio

from homeassistant.components.vacuum import (
    PLATFORM_SCHEMA, SUPPORT_BATTERY, SUPPORT_FAN_SPEED, SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF, SUPPORT_RETURN_HOME, SUPPORT_STATUS, SUPPORT_STOP, 
    SUPPORT_LOCATE, SUPPORT_CLEAN_SPOT, SUPPORT_START, VacuumDevice)
from homeassistant.const import (CONF_IP_ADDRESS, CONF_NAME, CONF_USERNAME, CONF_PASSWORD)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_ERROR = 'error'

DEFAULT_NAME = 'RoboVac'

PLATFORM = 'eufyrobovac'

FAN_SPEED_NORMAL = '0'
FAN_SPEED_MAX = '1'
FAN_SPEEDS = [FAN_SPEED_NORMAL, FAN_SPEED_MAX]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
}, extra=vol.ALLOW_EXTRA)

# Commonly supported features
SUPPORT_ROBOVAC = SUPPORT_BATTERY | SUPPORT_RETURN_HOME | SUPPORT_TURN_ON | \
                 SUPPORT_STATUS | SUPPORT_STOP | SUPPORT_TURN_OFF | \
                 SUPPORT_CLEAN_SPOT | SUPPORT_START | SUPPORT_LOCATE

async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Set up the Eufy RoboVac vacuum cleaner platform."""
    from robovac import Robovac, get_local_code
    if PLATFORM not in hass.data:
        hass.data[PLATFORM] = {}

    ip_address = config.get(CONF_IP_ADDRESS)
    eufy_username = config.get(CONF_USERNAME)
    eufy_password = config.get(CONF_PASSWORD)
    local_code = get_local_code(eufy_username, eufy_password, ip_address)
    name = config.get(CONF_NAME)

    eufy_robovac = Robovac(ip=ip_address, local_code=local_code)

    _LOGGER.debug("Initializing communication with host %s", ip_address)

    try:
        with async_timeout.timeout(9):
            await hass.async_add_job(eufy_robovac.connect)
    except (asyncio.TimeoutError, OSError):
        raise PlatformNotReady

    robovac_vac = RobovacVacuum(name, eufy_robovac)
    hass.data[PLATFORM][ip_address] = robovac_vac

    async_add_entities([robovac_vac], True)


class RobovacVacuum(VacuumDevice):
    """Representation of a Eufy RoboVac Vacuum cleaner robot."""
    def __init__(self, name, eufy_robovac):
            """Initialize the RoboVac handler."""
            self._available = False
            self._battery_level = None
            self._capabilities = {}
            self._fan_speed = None
            self._is_on = False
            self._name = name
            self._state_attrs = {}
            self._status = None
            self.vacuum = eufy_robovac
            self.vacuum_state = None

    @property
    def supported_features(self):
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORT_ROBOVAC

    @property
    def fan_speed(self):
        """Return the fan speed of the vacuum cleaner."""
        return self._fan_speed

    @property
    def fan_speed_list(self):
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return FAN_SPEEDS

    @property
    def battery_level(self):
        """Return the battery level of the vacuum cleaner."""
        return self._battery_level

    @property
    def status(self):
        """Return the status of the vacuum cleaner."""
        return self._status

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    async def async_turn_on(self, **kwargs):
        """Turn the vacuum on."""
        await self.hass.async_add_job(self.vacuum.start_auto_clean)
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        """Turn the vacuum off and return to home."""
        await self.async_stop()
        await self.async_return_to_base()

    async def async_stop(self, **kwargs):
        """Stop the vacuum cleaner."""
        await self.hass.async_add_job(self.vacuum.stop)
        self._is_on = False

    async def async_start(self, **kwargs):
        """Start the vacuum cleaner."""
        await self.hass.async_add_job(self.vacuum.start_auto_clean)
        self._is_on = False

    async def async_return_to_base(self, **kwargs):
        """Set the vacuum cleaner to return to the dock."""
        await self.hass.async_add_job(self.vacuum.go_home)
        self._is_on = False

    async def async_locate(self, **kwargs):
        """Locate the vacuum cleaner."""
        await self.hass.async_add_job(self.vacuum.start_find_me)

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set fan speed."""
        if fan_speed.capitalize() in FAN_SPEEDS:
            fan_speed = fan_speed.capitalize()
        else:
            _LOGGER.error("No such fan speed available: %s", fan_speed)
            return

        _LOGGER.debug("Set fan speed to: %s", fan_speed)
        if fan_speed == FAN_SPEED_NORMAL:
            await self.hass.async_add_job(self.vacuum.use_normal_speed)
        if fan_speed == FAN_SPEED_MAX:
            await self.hass.async_add_job(self.vacuum.use_max_speed)

    async def async_update(self):
        """Fetch state from the device."""
        try:
            state = self.vacuum.get_status()
            _LOGGER.debug("Got new state from the vacuum: %s", state)
            self.vacuum_state = state
            self._available = True

            possible_states = {
                0: 'Stopped',
                1: 'Spot cleaning',
                2: 'Cleaning',
                3: 'Returning to charging base',
                4: 'Edge cleaning',
                5: 'Cleaning single room'
            }

            self._battery_level = state.battery_capacity

            if self.vacuum_state.charger_status == 1:
                self._status = 'Charging'
            else:
                self._status = possible_states[self.vacuum_state.mode]

            self._is_on = self.vacuum_state.mode in [1,2,4,5]

            if state.error_code != 0:
                self._state_attrs[ATTR_ERROR] = state.error_code

            self._fan_speed = state.speed
        except Exception as e:
            _LOGGER.error("Failed to update RoboVac status: " + str(e))
