# onjuconfig

ESPHome (2026.11+) packages for the [Onju Voice](https://github.com/justLV/onju-voice) board as a Home Assistant voice satellite with microWakeWord.

- `nabu_duplex.yml`: the device package. One full duplex I2S bus, so the wake word keeps listening during playback.
- `nabu_micdebug.yml`: optional add-on that streams the microphones over UDP. Receive with `python3 tools/nabu_mic_rx.py`.

```yaml
substitutions:
  name: "onju-voice-1"
  friendly_name: "Nabu 1"
  api_key: !secret encryption_nabu1
  ota_password: !secret ota_nabu1
  twinkle_probability: "1%"
  device_description: "Onju Voice Satellite"
  project_version: "3.0.0"
  # micdebug_host: "192.168.0.x"   # only with the micdebug add-on

packages:
  onju: github://s00500/onjuconfig/nabu_duplex.yml@<commit>
  # micdebug: github://s00500/onjuconfig/nabu_micdebug.yml@<commit>
```

Also needs `wifi_ssid` / `wifi_password` secrets. The wake and error sounds live in `sounds/` and are fetched from this repo; override `wakeup_sound_file` / `error_sound_file` with a local path or another URL to use your own. `mute_on.flac` / `mute_off.flac` are the Voice PE `mute_switch_on` / `mute_switch_off` sounds from [esphome/home-assistant-voice-pe](https://github.com/esphome/home-assistant-voice-pe/tree/dev/sounds), trimmed to 0.6 / 0.8 s at 24 kHz to save flash. Tunables (mic gain, touch thresholds, ducking) are the substitutions at the top of `nabu_duplex.yml`.
