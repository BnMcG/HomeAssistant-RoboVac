# HomeAssistant-RoboVac
Component to implement Eufy RoboVac support in Home Assistant. Tested with the Eufy RoboVac 11c. Implemented using the standard
Vaacum platform for Home Assistant.

## Configuration
Add the following to your `configuration.yaml`:

```yaml
vacuum:
  - platform: eufyrobovac
    ip_address: 192.168.0.123
    local_code: ABCDEFGH
```

You may optionally provide a name for your RoboVac:

```yaml
vacuum:
  - platform: eufyrobovac
    name: NotARobot
    ip_address: 192.168.0.123
    local_code: ABCDEFGH
```

## Local Code
You must have the local code for your RoboVac. The easiest way to find this is to run the Eufy app while your
phone is connected with USB debugging. You can then use logcat and grep for the localCode value. It will be a 
16 character string.