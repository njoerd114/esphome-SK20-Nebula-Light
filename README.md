# ESPHome for Tuya SK20 WiFi Nebula Light

[![CI](https://github.com/njoerd114/esphome-SK20-Nebula-Light/actions/workflows/ci.yml/badge.svg)](https://github.com/njoerd114/esphome-SK20-Nebula-Light/actions/workflows/ci.yml)

This repository contains an ESPHome configuration for flashing ESPHome to Tuya SK20 nebula lights.
Thanks to the work of a lot of other people, no disassembly or soldering is required: you can jailbreak
the device with your laptop and flash ESPHome (or any other LibreTiny / WB3S-compatible firmware).

## References

The following repositories, projects and tools helped a lot in jailbreaking my nebula light:
- teardown, research and pictures: https://github.com/kireque/esphome_nebula_light
- basic/unfinished esphome config for included uC: https://github.com/fonix232/esphome_nebula_light
- exploit to flash tuya devices without disassembly: https://github.com/tuya-cloudcutter/tuya-cloudcutter
- esphome support for BK7231T devices: https://docs.libretiny.eu/
- tutorial on flashing esphome: https://docs.libretiny.eu/docs/flashing/tools/cloudcutter/
- discussion regarding the esphome configuration for this nebula device: https://github.com/kireque/esphome_nebula_light/issues/8

## Pictures

![](images/device-image.jpg)

![](images/esphome-screenshot.png)

## Basic instructions
This guide assumes you have a Linux computer and some basic terminal knowledge.
The used tools also have some prerequisites like `python`, `docker` and `plattform.io`.
Make sure you have [the esphome CLI](https://esphome.io/guides/getting_started_command_line) installed.

Configure your secrets by copying the template and filling it in:

```bash
$ cp secrets-template.yaml secrets.yaml
```

It needs your WiFi credentials and the API encryption key. `api_key` is the base64 key for the Home
Assistant API and for OTA updates, generate one with `openssl rand -base64 32`:

```yaml
wifi_ssid: "<your SSID>"
wifi_password: "<your wifi password>"
wifi_fallback_password: "<some random password>"
api_key: "<base64 encoded 32-byte key>"
```

Then build and flash the image using the following commands:

```bash
$ wget https://raw.githubusercontent.com/njoerd114/esphome-SK20-Nebula-Light/master/recommended_base.yaml
$ esphome compile recommended_base.yaml
$ git clone https://github.com/tuya-cloudcutter/tuya-cloudcutter
$ cp ./.esphome/build/nebula/.pioenvs/nebula/image_bk7231t_app.ota.ug.bin tuya-cloudcutter/custom-firmware/star_nebula_bk7231t.ota.ug.bin
$ sudo ./tuya-cloudcutter.sh
```

The last program will guide you through the jailbreaking procedure, asking you for the following information. You will also have to long press the device button for a few seconds twice until it is slow blinking (WiFi AP mode):
- (2) Flash 3rd Party Firmware
- By manufacturer/device name
- Tuya Generic
- SK20 Smart Star Projector
- 1.1.2 - BK7231T / oem_bk7231t_light3_laser_nanxin
- `star_nebula_bk7231t.ota.ug.bin`

The nebula light should now connect to your Wifi and/or host its own fallback AP.

## Slider calibration

The RGB channels and the laser do not emit any light below a minimum PWM duty, and the motor stalls
below a minimum speed. With the raw PWM values the bottom of every Home Assistant slider would do
nothing, and the laser would only start around the middle of its range.

The config remaps each range so the sliders start working where the hardware actually does something.
The thresholds are substitutions in `recommended_base.yaml`:

| substitution | default | controls |
|---|---|---|
| `rgb_min_power` | `20%` | RGB light channels |
| `laser_min_power` | `56%` | laser |
| `motor_min_power` | `15%` | motor |

These values differ between units, so measure your own device and adjust. Move the slider until the
laser starts lasing (or the light starts glowing) and set the matching substitution to that
percentage. `zero_means_zero` is enabled on those outputs, so turning a channel off still means a
real 0 instead of parking it at the threshold.

## Scenes

The Scene select exposes nine presets. The first five keep their original order, the rest were added:

- `Scene - Red`, `Scene - Blue`, `Scene - Green`, `Scene - White`, `Scene - Dimmed`
- `Scene - Red & Blue`, `Scene - Galaxy` (animated RGB), `Scene - Night Light`, `Scene - Party` (strobe)

Each static scene clears any running light effect, so a strobe or animation from a previous scene does
not leak into the next one. The light and the laser also expose their own effects (random, flicker,
strobe, pulse, twinkle, breathing) that you can pick independently in Home Assistant.

## Main Switch and state restore

The Main Switch represents whether the device is projecting (the light or the laser is on). The motor
alone projects nothing, so it is stopped automatically once the last light turns off.

Turning the Main Switch off does not forget what you had. The firmware snapshots which components were
active in RAM (no flash wear) and restores exactly that state when you turn it back on, including the
motor speed. After a reboot everything is restored on again.

## Home Assistant

The native API is enabled by default with encryption, so the device shows up in Home Assistant once
`api_key` is set in your secrets. If you do not use Home Assistant, comment the `api:` block out. IP
address, connected SSID, MAC address, uptime and WiFi signal are exposed as diagnostic entities.

## OTA updates

OTA updates are authenticated with the same `api_key` as the API. The plaintext `/update` endpoint is
not exposed: the web server OTA path is disabled (`web_server: ota: false`) and the captive portal is
left off, so every OTA listener is encrypted. The fallback AP from the `wifi` block is still available
for recovering from a bad WiFi configuration; connect to it and open the device IP in a browser to
reach the web UI.

## Development

The configuration is validated in CI on every push and pull request. The test suite checks the
structure of the YAML and runs the real `esphome config` command against the composed local packages:

```bash
$ pip install -r requirements-test.txt
$ pytest
```

## Local development

`recommended_base.yaml` fetches the package files from this repository over the network, so edits to
`nebula_light_device.yaml` or `platform_bk72xx.yaml` only take effect once they are pushed. While
developing, compile `local.yaml` instead, which includes the working-copy files directly:

```bash
$ esphome compile local.yaml
$ esphome upload local.yaml
```

## Versioning and releases

Releases are tagged with a calendar version in the form `YEAR.MONTH.PATCH` (for example `2026.10.0`),
starting at `0` for the first release in a month and incrementing afterwards. They are created
automatically after CI passes on `master`; the release job bumps `project.version` in
`recommended_base.yaml` to match the tag.

The configuration declares `project` metadata and requires ESPHome `2026.9.1` or newer (`min_version`),
which is the version it is tested against.
