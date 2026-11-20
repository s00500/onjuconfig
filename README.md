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
  timer_finished_sound_url: "http://homeassistant.local:8123/local/beep/timer_finished.mp3"
  # micdebug_host: "192.168.0.x"   # only with the micdebug add-on

packages:
  onju: github://s00500/onjuconfig/nabu_duplex.yml@<commit>
  # micdebug: github://s00500/onjuconfig/nabu_micdebug.yml@<commit>
```

Also needs `wifi_ssid` / `wifi_password` secrets and `beep.flac` / `error24.flac` next to the device config. Tunables (mic gain, touch thresholds, ducking) are the substitutions at the top of `nabu_duplex.yml`.
