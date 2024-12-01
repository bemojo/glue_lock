# Glue Lock Integration for Home Assistant

[![hacs][hacsbadge]][hacs] [![IoT Class][iotbadge]][iot]

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://github.com/hacs/integration
[iotbadge]: https://img.shields.io/badge/IoT%20Class-Cloud%20Polling-blue.svg
[iot]: https://www.home-assistant.io/blog/2016/02/12/classifying-the-internet-of-things/#cloud-polling

Home Assistant integration for Glue Lock smart locks. Control and monitor your Glue locks directly from Home Assistant.

## Features

- Lock/unlock control
- Real-time state monitoring
- Battery level tracking
- Connection status
- Event history

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the "+" button
4. Search for "Glue Lock"
5. Click "Download"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/glue_lock` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings -> Devices & Services
2. Click "Add Integration"
3. Search for "Glue Lock"
4. Follow the configuration steps

## Usage

After configuration, your Glue locks will appear as lock entities in Home Assistant. You can:

- Lock/unlock from the UI
- Create automations
- Add to scripts
- Monitor status

## Support

- Report issues on [GitHub](https://github.com/bemojo/glue_lock/issues)
- Join the discussion on [Home Assistant Community](https://community.home-assistant.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
