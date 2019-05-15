# HomeAssistant-RoboVac
Component to implement Eufy RoboVac support in Home Assistant. Tested with the Eufy RoboVac 11c. Implemented using the standard
Vaacum platform for Home Assistant.

## Configuration
Add the following to your `configuration.yaml`:

```yaml
vacuum:
  - platform: eufyrobovac
    ip_address: 192.168.0.123
    username: your_eufy_username
    password: your_eufy_password
```

You may optionally provide a name for your RoboVac:

```yaml
vacuum:
  - platform: eufyrobovac
    name: NotARobot
    ip_address: 192.168.0.123
    username: your_eufy_username
    password: your_eufy_password
```

## Why do you need my Eufy credentials?
Each Eufy RoboVac has its own 'local code' - this is essentially a password that the app uses to authenticate with the RoboVac.
This code can be retrieved from the Eufy API by logging in with your username and password, and finding the device using its IP address. 
By providing the component with your username and password, this can be done automatically.