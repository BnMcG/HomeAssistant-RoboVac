""" 
Eufy RoboVac integration.

This component allows Home Assistant to control Eufy RoboVac smart vacuum cleaners. It will also report the current
state of any connected RoboVacs. This component has been tested with the Eufy RoboVac 11c, but may work with other devices.

Configuration:

Add the following to your configuration.yaml file:

vacuum:
  - platform: eufyrobovac
    ip_address: 192.168.0.123
    username: eufy_username
    password: eufy_password
"""