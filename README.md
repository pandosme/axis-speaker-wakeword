# Axis Speaker Wakeword Monitor

A Python-based middleware service that monitors audio from Axis network speakers/devices for wake word detection and voice activity, triggering the [Voice ACAP](https://github.com/pandosme/Voice) for Speech-to-Text (STT) and Text-to-Speech (TTS) processing.

## Overview

This service acts as a bridge between Axis network audio devices and the Voice ACAP application. It continuously monitors audio streams via RTSP, detects wake words using Porcupine, and uses Voice Activity Detection (VAD) to determine when a user has finished speaking. MQTT messages are published to trigger the Voice ACAP for STT/TTS processing.

### Architecture

```
┌─────────────────┐         RTSP          ┌──────────────────────┐
│ Axis Speaker    │◄──────────────────────│ Wakeword Monitor     │
│ (kontoret)      │                       │ - Porcupine Wake Word│
└─────────────────┘                       │ - Silero VAD         │
                                          │ - MQTT Publisher     │
┌─────────────────┐         RTSP          └──────────┬───────────┘
│ Axis Speaker    │◄──────────────────────           │
│ (kitchen)       │                                  │ MQTT
└─────────────────┘                                  │
                                                     ▼
                                           ┌──────────────────────┐
                                           │ MQTT Broker          │
                                           │ (192.168.0.57:1883)  │
                                           └──────────┬───────────┘
                                                      │
                                                      │ MQTT Topics
                                                      │
                                           ┌──────────▼───────────┐
                                           │ Voice ACAP           │
                                           │ - STT (Whisper)      │
                                           │ - TTS (ElevenLabs)   │
                                           │ - LLM Integration    │
                                           └──────────────────────┘
```

## Features

- **Multi-device support**: Monitor multiple Axis speakers simultaneously
- **Wake word detection**: Uses Porcupine for accurate wake word detection
- **Voice Activity Detection**: Silero VAD to detect when user stops speaking
- **Configurable timing**:
  - Minimum recording time (prevents premature cutoff)
  - Maximum recording time (timeout protection)
  - Silence duration threshold
- **MQTT integration**: Publishes events to trigger Voice ACAP
- **Low latency**: RTSP streaming with FFmpeg for real-time audio processing

## Prerequisites

### Hardware
- Axis network speaker or device with audio support (e.g., Axis C8210 Network Audio Bridge)
- Network connectivity between monitor and Axis devices
- MQTT broker (Mosquitto recommended)

### Software
- Python 3.8 or higher
- FFmpeg installed and in PATH
- [Porcupine Access Key](https://console.picovoice.ai/) (free tier available)
- [Voice ACAP](https://github.com/pandosme/Voice) installed on Axis device

### Voice ACAP
This service is designed to work with the Voice ACAP developed by pandosme, which provides:
- **Speech-to-Text** using Wyoming whisper
- **Text-to-Speech** using Wyoming piper
- **MQTT control interface**

For Voice ACAP installation and configuration, visit: https://github.com/pandosme/Voice

## Installation

### 1. Install FFmpeg

**Ubuntu/Debian:**
```
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

### 2. Clone Repository

```
git clone https://github.com/yourusername/axis-speaker-wakeword.git
cd axis-speaker-wakeword
```

### 3. Create Python Virtual Environment

```
python3 -m venv wakeword
source wakeword/bin/activate  # On Windows: wakeword\Scripts\activate
```

### 4. Install Python Dependencies

```
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file from the example template:

```
cp .env.example .env
```

Then edit `.env` and configure:

```
# Axis Device Credentials (shared across all devices)
AXIS_USERNAME=root
AXIS_PASSWORD=your_axis_password

# MQTT Broker
MQTT_BROKER=192.168.1.17
MQTT_PORT=1883

# Porcupine API Key (see below for how to get one)
PORCUPINE_ACCESS_KEY=your_porcupine_access_key_here
```

**Note:** Device hostnames/IPs are configured in `config.yaml`, not in `.env`.

#### Getting a Porcupine Access Key

This project uses [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/) for wake word detection.

1. Visit https://console.picovoice.ai/
2. Sign up or log in to your account
3. Navigate to the **Access Keys** section
4. Click **Create new access key**
5. Give it a name (e.g., `axis-wakeword`) and create it
6. Copy the generated key
7. Paste it into your `.env` file as `PORCUPINE_ACCESS_KEY`

**Free tier includes:** 3 wake words, unlimited devices, perfect for home automation use cases.

### 6. Configure Devices and MQTT

Copy the example configuration:

```
cp config.yaml.example config.yaml
```

Edit `config.yaml` and configure your Axis devices:

```
# Axis Device Configuration
axis:
  devices:
    - name: "Kontoret"
      id: "ACCC8EF67F46"
      address: "http://speaker-kontoret.internal"  # Or IP: http://192.168.1.100
      audio_source: 0
      
    # Add more devices as needed
    # - name: "Köket"
    #   id: "ACCC8EF67F47"
    #   address: "http://speaker-kitchen.internal"
    #   audio_source: 0

# MQTT Configuration
mqtt:
  broker: "http://192.168.1.80"  # Your MQTT broker IP
  port: 1883
  client_id_prefix: "axis_audio_service"
  topics:
    wakeword: "voice/listen/start/{device_id}"
    vad_stop: "voice/listen/stop/{device_id}"
  qos: 1
  retain: false

# VAD Configuration
vad:
  threshold: 0.5
  min_recording_time_ms: 1500  # Don't detect silence for first 1.5 seconds
  min_silence_duration_ms: 800 # 800ms of silence triggers stop
  max_recording_time_ms: 7000  # Force stop after 7 seconds
```

## Usage

### Start the Service

```
python axis-audio-service.py
```

### Expected Output

```
============================================================
Multi-Device Wakeword Monitor
============================================================
✓ Loaded config.yaml
  Found 2 device(s) configured
✓ MQTT connected to 192.168.0.57:1883
Loading Silero VAD (shared)...
✓ Silero VAD initialized
  Threshold: 0.5
  Min recording: 1500ms
  Silence duration: 800ms
  Max recording: 7000ms

============================================================
Initializing: Kontoret (ID: kontoret)
============================================================
  ✓ Porcupine: 'porcupine' (sensitivity: 0.5)
  🎤 Starting RTSP stream from speaker-kontoret.internal
  ✓ RTSP stream connected (16kHz mono PCM)
✓ Kontoret ready!
  MQTT topics:
    Wakeword: voice/listen/start/kontoret
    VAD Stop: voice/listen/stop/kontoret

============================================================
✓ All systems ready - 2 device(s) active
============================================================
Active devices:
  -  Kontoret (kontoret) @ speaker-kontoret.internal
  -  Köket (kitchen) @ speaker-kitchen.internal

Press Ctrl+C to stop
============================================================

[kontoret] 🎧 Audio processing started - listening for wakeword...
[kitchen] 🎧 Audio processing started - listening for wakeword...
```

### When Wake Word is Detected

```
[kontoret] 📢 WAKEWORD DETECTED! → voice/listen/start/kontoret
[kontoret] 🎙️  Recording (min:1.5s, max:7.0s)
[kontoret] 🔇 SILENCE (3.2s)! → voice/listen/stop/kontoret
```

## MQTT Topics

### Published Topics

| Topic | Payload | Description |
|-------|---------|-------------|
| `voice/listen/start/{device_id}` | `DETECTED` | Wake word detected, start listening |
| `voice/listen/stop/{device_id}` | `SILENCE` | User finished speaking (silence or timeout) |

### Voice ACAP Integration

The Voice ACAP should subscribe to these topics and:

1. **On `voice/listen/start/{device_id}`**: Begin recording audio and prepare for STT
2. **On `voice/listen/stop/{device_id}`**: Stop recording, process with STT, send to LLM, and respond with TTS

## Configuration Options

### VAD Timing Parameters

- **`min_recording_time_ms`**: Minimum time before VAD can trigger (prevents cutting off user)
  - Default: 1500ms (1.5 seconds)
  - Increase if users get cut off too early
  
- **`min_silence_duration_ms`**: How long silence must persist to end recording
  - Default: 800ms
  - Decrease for faster response, increase if it stops too quickly
  
- **`max_recording_time_ms`**: Maximum recording time before forcing stop (safety timeout)
  - Default: 7000ms (7 seconds)
  - Prevents infinite recording if silence detection fails

### Wake Word Options

Supported wake words (`wakeword.model` in config.yaml):
- `porcupine` (default)
- `jarvis`
- `alexa`
- `hey_google`
- `computer`

**Wake word sensitivity** (`wakeword.threshold`):
- Range: 0.0 to 1.0
- Default: 0.5
- Higher = more sensitive (more false positives)
- Lower = less sensitive (may miss wake words)

### Adding More Devices

Simply add another device block in `config.yaml`:

```
axis:
  devices:
    - name: "Living Room"
      id: "ACCC8EF67F46"
      address: "http://192.168.1.101"
      audio_source: 0
      
    - name: "Bedroom"
      id: "ACCC8EF67F47"
      address: "http://bedroom-speaker.local"
      audio_source: 0
```

## Troubleshooting

### RTSP Connection Fails

**Symptoms:** `❌ RTSP stream failed` or connection timeout

**Solutions:**
- Verify Axis device IP/hostname is correct in `config.yaml`
- Check Axis credentials in `.env` are correct
- Ensure RTSP is enabled on Axis device (usually enabled by default)
- Test RTSP URL manually with FFplay:
  ```
  ffplay rtsp://root:password@192.168.1.100/axis-media/media.amp?audio=1
  ```
- Check network connectivity: `ping speaker-kontoret.internal`
- Verify firewall is not blocking RTSP (port 554)

### No Wake Word Detection

**Symptoms:** Wake word spoken but no detection

**Solutions:**
- Speak clearly and say the wake word ("Porcupine" by default)
- Adjust `wakeword.threshold` in `config.yaml` (try 0.6 or 0.7 for higher sensitivity)
- Check audio levels on Axis device (ensure microphone is working)
- Verify Porcupine access key is valid in `.env`
- Try a different wake word (e.g., change to `jarvis`)
- Check logs for Porcupine initialization errors

### MQTT Connection Issues

**Symptoms:** `❌ MQTT connection failed`

**Solutions:**
- Verify MQTT broker is running:
  ```
  mosquitto_sub -h 192.168.0.57 -t '#' -v
  ```
- Check broker IP and port in `config.yaml`
- Ensure no firewall blocking port 1883
- Test MQTT manually:
  ```
  mosquitto_pub -h 192.168.0.57 -t test -m "hello"
  ```
- Check MQTT broker logs for connection errors

### VAD Cuts Off Too Early

**Symptoms:** Recording stops before user finishes speaking

**Solutions:**
- Increase `min_recording_time_ms` (e.g., 2000 or 2500)
- Decrease `vad.threshold` (e.g., 0.3 or 0.4)
- Increase `min_silence_duration_ms` (e.g., 1000 or 1200)

### VAD Doesn't Detect Silence

**Symptoms:** Recording continues indefinitely or hits max timeout

**Solutions:**
- Increase `vad.threshold` (e.g., 0.6 or 0.7)
- Decrease `min_silence_duration_ms` (e.g., 600 or 500)
- Check for background noise affecting VAD
- Verify max timeout is working (should stop at `max_recording_time_ms`)

### FFmpeg Not Found

**Symptoms:** `ffmpeg: command not found`

**Solutions:**
- Install FFmpeg (see Installation section)
- Verify FFmpeg is in PATH:
  ```
  which ffmpeg
  ffmpeg -version
  ```
- On Windows, add FFmpeg directory to system PATH

## Development

### Project Structure

```
axis-speaker-wakeword/
├── axis-audio-service.py   # Main service
├── config.yaml              # Configuration (gitignored)
├── config.yaml.example      # Configuration template
├── .env                     # Credentials (gitignored)
├── .env.example             # Credentials template
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── .gitignore              # Git ignore rules
```

### Running as a Service (Systemd)

Create `/etc/systemd/system/axis-wakeword.service`:

```
[Unit]
Description=Axis Wakeword Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/axis-speaker-wakeword
ExecStart=/path/to/axis-speaker-wakeword/wakeword/bin/python axis-audio-service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```
sudo systemctl enable axis-wakeword
sudo systemctl start axis-wakeword
sudo systemctl status axis-wakeword
```

View logs:
```
sudo journalctl -u axis-wakeword -f
```

## License

MIT License

## Credits

- **Voice ACAP**: [pandosme/Voice](https://github.com/pandosme/Voice)
- **Porcupine Wake Word**: [Picovoice](https://picovoice.ai/)
- **Silero VAD**: [snakers4/silero-vad](https://github.com/snakers4/silero-vad)
- **ACAP Development**: [Axis Communications](https://www.axis.com/products/acap)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues related to:
- **This service**: Open an issue on this repository
- **Voice ACAP**: Visit https://github.com/pandosme/Voice
- **Axis devices**: Contact Axis Support or check [Axis Developer Community](https://www.axis.com/developer-community)
- **Porcupine**: Visit [Picovoice Console](https://console.picovoice.ai/) or [documentation](https://picovoice.ai/docs/)
```

**config.yaml.example:**

```yaml
# ============================================================================
# Axis Speaker Wakeword Monitor Configuration
# ============================================================================
# This is a template configuration file. Copy it to config.yaml and customize.
#
# Quick start:
#   cp config.yaml.example config.yaml
#   nano config.yaml  # Edit with your device addresses and settings
#
# ============================================================================

# ============================================================================
# Axis Device Configuration
# ============================================================================
# Configure one or more Axis network speakers or audio bridges.
# Each device will be monitored independently for wake word detection.
#
# Required fields:
#   name: Human-readable name for the device
#   id: Unique identifier used in MQTT topics (lowercase, no spaces)
#   address: HTTP URL or IP address of the Axis device
#   audio_source: Audio input source (0 for built-in microphone)
#
axis:
  devices:
    # First device (office)
    - name: "Kontoret"
      id: "ACCC8EF67F46"
      address: "http://speaker-kontoret.internal"  # Or use IP: http://192.168.1.100
      audio_source: 0
      
    # Additional devices (uncomment and customize as needed)
    # - name: "Köket"
    #   id: "ACCC8EF67F47"
    #   address: "http://speaker-kitchen.internal"
    #   audio_source: 0
    #
    # - name: "Living Room"
    #   id: "ACCC8EF67F48"
    #   address: "http://192.168.1.101"
    #   audio_source: 0
    #
    # - name: "Bedroom"
    #   id: "ACCC8EF67F49"
    #   address: "http://bedroom-speaker.local"
    #   audio_source: 0

# ============================================================================
# MQTT Configuration
# ============================================================================
# MQTT broker settings for communication with Voice ACAP.
#
# The service publishes to:
#   - voice/listen/start/{device_id}  (when wake word is detected)
#   - voice/listen/stop/{device_id}   (when user stops speaking)
#
mqtt:
  broker: "192.168.0.57"  # MQTT broker hostname or IP
  port: 1883             # MQTT broker port (default: 1883)
  client_id_prefix: "axis_audio_service"  # MQTT client ID prefix
  topics:
    wakeword: "voice/listen/start/{device_id}"  # Wake word detected topic
    vad_stop: "voice/listen/stop/{device_id}"   # Silence detected topic
  qos: 1        # Quality of Service (0, 1, or 2)
  retain: false # Retain MQTT messages

# ============================================================================
# Audio Processing Configuration
# ============================================================================
# Audio stream settings (usually no need to change these)
#
audio:
  sample_rate: 16000      # Audio sample rate in Hz
  codec: "g711"           # Audio codec
  bitrate: 32000          # Audio bitrate
  chunk_duration: 0.08    # Audio chunk duration in seconds

# ============================================================================
# Wake Word Configuration (Porcupine)
# ============================================================================
# Wake word detection settings.
#
# Available wake words:
#   - porcupine (default)
#   - jarvis
#   - alexa
#   - hey_google
#   - computer
#
# Threshold (sensitivity):
#   - Range: 0.0 to 1.0
#   - Higher = more sensitive (more false positives)
#   - Lower = less sensitive (may miss wake words)
#   - Recommended: 0.5
#
wakeword:
  model: "porcupine"         # Wake word to use
  threshold: 0.5             # Detection sensitivity (0.0-1.0)
  inference_framework: "onnx"

# ============================================================================
# VAD (Voice Activity Detection) Configuration
# ============================================================================
# Voice Activity Detection settings using Silero VAD.
#
# Timing parameters:
#   - min_recording_time_ms: Minimum time before VAD can trigger
#       * Prevents cutting off user too early
#       * Increase if users get cut off mid-sentence
#       * Default: 1500ms (1.5 seconds)
#
#   - min_silence_duration_ms: Silence duration to end speech
#       * How long silence must persist to stop recording
#       * Decrease for faster response
#       * Increase if it stops too quickly
#       * Default: 800ms
#
#   - max_recording_time_ms: Maximum recording time (safety timeout)
#       * Forces stop if silence detection fails
#       * Prevents infinite recording
#       * Default: 7000ms (7 seconds)
#
# Threshold:
#   - Speech probability threshold (0.0-1.0)
#   - Higher = requires clearer speech (less noise tolerance)
#   - Lower = more noise tolerance (may not detect silence)
#   - Default: 0.5
#
vad:
  threshold: 0.5                  # Speech probability threshold (0.0-1.0)
  min_recording_time_ms: 1500     # Minimum recording time (no early cutoff)
  min_silence_duration_ms: 800    # Silence duration to end speech
  max_recording_time_ms: 7000     # Maximum recording time (safety timeout)
  speech_pad_ms: 30               # Padding around speech segments

# ============================================================================
# Service Configuration
# ============================================================================
# General service settings (usually no need to change)
#
service:
  log_level: "INFO"              # Log level: DEBUG, INFO, WARNING, ERROR
  reconnect_delay: 5             # Seconds between reconnection attempts
  health_check_interval: 60      # Seconds between health checks
```
