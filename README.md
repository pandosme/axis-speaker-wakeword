## README.md

# Axis Speaker Wakeword Monitor

A Python-based middleware service that monitors audio from Axis network speakers/devices for wake word detection and voice activity, triggering the [Voice ACAP](https://github.com/pandosme/Voice) for Speech-to-Text (STT) and Text-to-Speech (TTS) processing.

## Overview

This service acts as a bridge between Axis network audio devices and the Voice ACAP application. It continuously monitors audio streams via RTSP, detects wake words using Porcupine, and uses Voice Activity Detection (VAD) to determine when a user has finished speaking. MQTT messages are published to trigger the Voice ACAP for STT/TTS processing.

### How It Works

```
┌─────────────────┐         RTSP          ┌──────────────────────┐
│ Axis Speaker    │◄──────────────────────│ Wakeword Monitor     │
│ (Office)        │                        │ - Porcupine Wake Word│
└─────────────────┘                        │ - Silero VAD         │
                                           │ - MQTT Publisher     │
┌─────────────────┐         RTSP          └──────────┬───────────┘
│ Axis Speaker    │◄──────────────────────           │
│ (Kitchen)       │                                   │ MQTT
└─────────────────┘                                   │
                                                      ▼
                                           ┌──────────────────────┐
                                           │ MQTT Broker          │
                                           │ (192.168.1.80:1883)  │
                                           └──────────┬───────────┘
                                                      │
                                                      │ Topics:
                                                      │ voice/listen/start/{device_id}
                                                      │ voice/listen/stop/{device_id}
                                                      │
                                           ┌──────────▼───────────┐
                                           │ Voice ACAP           │
                                           │ - STT (Whisper)      │
                                           │ - TTS (Piper)        │
                                           │ - LLM Integration    │
                                           └──────────────────────┘
```

## Features

- **Multi-device support**: Monitor multiple Axis speakers simultaneously
- **Wake word detection**: Uses Picovoice Porcupine for accurate wake word detection
- **Voice Activity Detection**: Silero VAD to detect when user stops speaking
- **Configurable timing**:
  - Minimum recording time (prevents premature cutoff)
  - Maximum recording time (timeout protection)
  - Silence duration threshold
- **MQTT integration**: Publishes events to trigger Voice ACAP
- **Low latency**: RTSP streaming with FFmpeg for real-time audio processing
- **Easy setup**: Automated installation with conda environment management

## Prerequisites

### Hardware
- **Axis network speaker** or device with audio support
  - Examples: Axis C8210 Network Audio Bridge, Axis speakers with built-in microphones
- **Network connectivity** between monitor and Axis devices
- **MQTT broker** (Mosquitto recommended)
- Server or computer to run the service (Linux, macOS, or Windows with WSL)

### Software
- **Conda** (Miniconda or Anaconda)
- **FFmpeg** (installed automatically by `install.sh` on Linux/macOS)
- **Porcupine Access Key** (free tier available at https://console.picovoice.ai/)
- **Voice ACAP** installed on Axis device (optional but recommended)

### Voice ACAP
This service is designed to work with the [Voice ACAP](https://github.com/pandosme/Voice) developed by pandosme, which provides:
- **Speech-to-Text** using Wyoming Whisper
- **Text-to-Speech** using Wyoming Piper
- **MQTT control interface**
- **LLM integration** for conversational AI

For Voice ACAP installation and configuration, visit: https://github.com/pandosme/Voice

## Quick Start

```
# 1. Clone the repository
git clone https://github.com/pandosme/axis-speaker-wakeword.git
cd axis-speaker-wakeword

# 2. Run the installation script (creates conda env + installs dependencies)
bash install.sh

# 3. Activate the environment
conda activate wakeword

# 4. Run the setup wizard
python setup.py

# 5. Start the service
python app.py
```

That's it! The service will start monitoring for wake words.

## Detailed Installation

### Step 1: Install Conda (if not already installed)

**Linux:**
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
```

**macOS:**
```
brew install miniconda
conda init "$(basename "${SHELL}")"
```

**Windows:**
Download and install from: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Clone Repository

```
git clone https://github.com/pandosme/axis-speaker-wakeword.git
cd axis-speaker-wakeword
```

### Step 3: Run Installation Script

```
bash install.sh
```

This script will:
- Check if conda is installed
- Install FFmpeg (on Linux/macOS)
- Create a conda environment named `wakeword`
- Install Python 3.10
- Install all required dependencies (torch, porcupine, etc.)

### Step 4: Activate Environment

```
conda activate wakeword
```

### Step 5: Configure the Service

**Option A: Interactive Setup Wizard (Recommended)**
```
python setup.py
```

The wizard will ask for:
- Axis device credentials (username/password)
- Axis device address (IP or hostname)
- MQTT broker details
- MQTT authentication (if required)
- Porcupine API key

**Option B: Manual Configuration**
```
# Copy template files
cp .env.example .env
cp config.yaml.example config.yaml

# Edit configuration files
nano .env
nano config.yaml
```

### Step 6: Get Porcupine Access Key

1. Visit https://console.picovoice.ai/
2. Sign up or log in
3. Go to **Access Keys** section
4. Click **Create new access key**
5. Name it (e.g., "axis-wakeword")
6. Copy the generated key
7. Paste it into your `.env` file as `PORCUPINE_ACCESS_KEY`

**Free tier includes:** 3 wake words, unlimited devices

### Step 7: Run the Service

```
python app.py
```

## Configuration

### Environment Variables (.env)

```
# Axis Device Credentials (shared across all devices)
AXIS_USERNAME=root
AXIS_PASSWORD=your_password

# MQTT Broker
MQTT_BROKER=192.168.1.80
MQTT_PORT=1883

# MQTT Authentication (optional)
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_pass

# Porcupine Access Key
PORCUPINE_ACCESS_KEY=your_key_here
```

### Device Configuration (config.yaml)

```
# Axis Devices
axis:
  devices:
    - name: "Office"
      id: "office"
      address: "http://192.168.1.100"
      audio_source: 0
      
    - name: "Kitchen"
      id: "kitchen"
      address: "http://192.168.1.101"
      audio_source: 0

# MQTT Configuration
mqtt:
  broker: "192.168.1.80"
  port: 1883
  client_id_prefix: "axis_audio_service"
  topics:
    wakeword: "voice/listen/start/{device_id}"
    vad_stop: "voice/listen/stop/{device_id}"
  qos: 1
  retain: false

# Wake Word Settings
wakeword:
  model: "porcupine"  # Options: porcupine, jarvis, alexa, hey_google, computer
  threshold: 0.5      # 0.0-1.0 (higher = more sensitive)
  inference_framework: "onnx"

# Voice Activity Detection
vad:
  threshold: 0.5                  # Speech probability threshold
  min_recording_time_ms: 1500     # Min time before VAD triggers
  min_silence_duration_ms: 800    # Silence duration to end speech
  max_recording_time_ms: 7000     # Max recording time (safety timeout)
  speech_pad_ms: 30               # Padding around speech
```

## Usage

### Starting the Service

```
# Activate conda environment
conda activate wakeword

# Run the service
python app.py
```

### Expected Output

```
============================================================
Multi-Device Wakeword Monitor
============================================================
✓ Loaded config.yaml
  Found 2 device(s) configured
✓ MQTT connected to 192.168.1.80:1883
Loading Silero VAD (shared)...
✓ Silero VAD initialized
  Threshold: 0.5
  Min recording: 1500ms
  Silence duration: 800ms
  Max recording: 7000ms

============================================================
Initializing: Office (ID: office)
============================================================
  ✓ Porcupine: 'porcupine' (sensitivity: 0.5)
  🎤 Starting RTSP stream from 192.168.1.100
  ✓ RTSP stream connected (16kHz mono PCM)
✓ Office ready!
  MQTT topics:
    Wakeword: voice/listen/start/office
    VAD Stop: voice/listen/stop/office

============================================================
✓ All systems ready - 2 device(s) active
============================================================
Active devices:
  -  Office (office) @ 192.168.1.100
  -  Kitchen (kitchen) @ 192.168.1.101

Press Ctrl+C to stop
============================================================

[office] 🎧 Audio processing started - listening for wakeword...
[kitchen] 🎧 Audio processing started - listening for wakeword...
```

### When Wake Word is Detected

```
[office] 📢 WAKEWORD DETECTED! → voice/listen/start/office
[office] 🎙️  Recording (min:1.5s, max:7.0s)
[office] 🔇 SILENCE (3.2s)! → voice/listen/stop/office
```

## MQTT Topics

### Published Topics

| Topic | Payload | When Published | Description |
|-------|---------|----------------|-------------|
| `voice/listen/start/{device_id}` | `DETECTED` | Wake word detected | Signals Voice ACAP to start listening |
| `voice/listen/stop/{device_id}` | `SILENCE` | Silence detected or timeout | Signals Voice ACAP to process speech |

### Monitoring MQTT Messages

```
# Subscribe to all voice topics
mosquitto_sub -h 192.168.1.80 -t 'voice/#' -v

# Subscribe to specific device
mosquitto_sub -h 192.168.1.80 -t 'voice/listen/+/office' -v
```

## Configuration Options

### VAD Timing Parameters

**`min_recording_time_ms`** (Default: 1500)
- Minimum time before VAD can trigger
- Prevents cutting off user too early
- Increase if users get interrupted mid-sentence
- Range: 500-3000ms

**`min_silence_duration_ms`** (Default: 800)
- How long silence must persist to end recording
- Decrease for faster response
- Increase if it stops too quickly during pauses
- Range: 300-2000ms

**`max_recording_time_ms`** (Default: 7000)
- Maximum recording time before forcing stop
- Safety timeout if silence detection fails
- Range: 5000-15000ms

### Wake Word Options

**Available wake words:**
- `porcupine` (default) - "Porcupine"
- `jarvis` - "Jarvis"
- `alexa` - "Alexa"
- `hey_google` - "Hey Google"
- `computer` - "Computer"

**Wake word sensitivity (`threshold`):**
- Range: 0.0 to 1.0
- Default: 0.5
- Higher = more sensitive (more false positives)
- Lower = less sensitive (may miss wake words)
- Recommended: 0.4-0.6

### Adding More Devices

Edit `config.yaml` and add device blocks:

```
axis:
  devices:
    - name: "Living Room"
      id: "living_room"
      address: "http://192.168.1.102"
      audio_source: 0
      
    - name: "Bedroom"
      id: "bedroom"
      address: "http://bedroom-speaker.local"
      audio_source: 0
```

Each device will be monitored independently with its own MQTT topics.

## Running as a Service

### Systemd Service (Linux)

Create `/etc/systemd/system/axis-wakeword.service`:

```
[Unit]
Description=Axis Wakeword Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/axis-speaker-wakeword
Environment="PATH=/home/your_username/miniconda3/envs/wakeword/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/your_username/miniconda3/envs/wakeword/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Update paths:**
- Replace `your_username` with your actual username
- Update conda path if different (find with `conda info --base`)

**Enable and start:**
```
sudo systemctl daemon-reload
sudo systemctl enable axis-wakeword
sudo systemctl start axis-wakeword
sudo systemctl status axis-wakeword
```

**View logs:**
```
sudo journalctl -u axis-wakeword -f
```

**Stop service:**
```
sudo systemctl stop axis-wakeword
```

## Troubleshooting

### RTSP Connection Fails

**Symptoms:** `❌ RTSP stream failed` or connection timeout

**Solutions:**
1. Verify device IP/hostname in `config.yaml`
2. Check Axis credentials in `.env`
3. Test RTSP manually:
   ```
   ffplay rtsp://root:password@192.168.1.100/axis-media/media.amp?audio=1
   ```
4. Ensure RTSP is enabled on Axis device (usually default)
5. Check network connectivity: `ping 192.168.1.100`
6. Verify firewall isn't blocking RTSP (port 554)

### No Wake Word Detection

**Symptoms:** Wake word spoken but no detection

**Solutions:**
1. Speak clearly and say the wake word ("Porcupine" by default)
2. Increase `wakeword.threshold` (try 0.6 or 0.7)
3. Check audio levels on Axis device
4. Verify Porcupine key is valid in `.env`
5. Try different wake word (change to `jarvis`)
6. Check distance from microphone (optimal: 1-3 meters)

### MQTT Connection Issues

**Symptoms:** `❌ MQTT connection failed`

**Solutions:**
1. Verify MQTT broker is running:
   ```
   mosquitto_sub -h 192.168.1.80 -t '#' -v
   ```
2. Check broker IP in `config.yaml`
3. Verify MQTT credentials if authentication is enabled
4. Check firewall (port 1883)
5. Test MQTT manually:
   ```
   mosquitto_pub -h 192.168.1.80 -t test -m "hello"
   ```

### VAD Cuts Off Too Early

**Symptoms:** Recording stops before user finishes speaking

**Solutions:**
1. Increase `min_recording_time_ms` (e.g., 2000 or 2500)
2. Decrease `vad.threshold` (e.g., 0.3 or 0.4)
3. Increase `min_silence_duration_ms` (e.g., 1000 or 1200)

### VAD Doesn't Detect Silence

**Symptoms:** Recording continues or hits max timeout

**Solutions:**
1. Increase `vad.threshold` (e.g., 0.6 or 0.7)
2. Decrease `min_silence_duration_ms` (e.g., 600)
3. Check for background noise
4. Ensure max timeout is appropriate

### Conda Environment Issues

**Symptoms:** Import errors, wrong Python version

**Solutions:**
1. Verify environment is activated:
   ```
   conda activate wakeword
   which python  # Should show wakeword env
   ```
2. Reinstall environment:
   ```
   conda env remove -n wakeword
   bash install.sh
   ```
3. Check environment packages:
   ```
   conda list
   ```

### FFmpeg Not Found

**Symptoms:** `ffmpeg: command not found`

**Solutions:**
1. Install FFmpeg:
   ```
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```
2. Verify installation:
   ```
   which ffmpeg
   ffmpeg -version
   ```

## Development

### Project Structure

```
axis-speaker-wakeword/
├── app.py                   # Main application
├── setup.py                 # Interactive setup wizard
├── install.sh               # Installation script
├── environment.yml          # Conda environment specification
├── .env                     # Environment variables (gitignored)
├── .env.example             # Environment template
├── config.yaml              # Configuration (gitignored)
├── config.yaml.example      # Configuration template
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── INSTALL.md               # Detailed installation guide
└── TROUBLESHOOTING.md       # Troubleshooting guide
```

### Testing Changes

```
# Activate environment
conda activate wakeword

# Run with debug logging
# (modify config.yaml: service.log_level: "DEBUG")
python app.py
```

### Updating Dependencies

```
# Update environment.yml, then:
conda env update -f environment.yml --prune
```

## Performance

- **CPU Usage:** ~5-10% per device (depends on CPU)
- **Memory:** ~200-300MB per device
- **Network:** ~128 kbps per device (RTSP audio stream)
- **Latency:** <100ms wake word detection, <200ms VAD detection

## Security Considerations

- **Credentials:** Never commit `.env` or `config.yaml` to git
- **MQTT:** Use MQTT authentication in production
- **Network:** Consider VLAN isolation for IoT devices
- **Updates:** Keep dependencies updated for security patches

## FAQ

**Q: Can I use multiple wake words?**
A: Free Porcupine tier supports 3 wake words. You can configure different wake words per device.

**Q: Does this work with Axis cameras?**
A: Yes, if the camera has audio input (built-in or external microphone).

**Q: Can I run multiple instances?**
A: Yes, use different MQTT client IDs and ensure no device overlap.

**Q: What's the range for wake word detection?**
A: Optimal: 1-3 meters. Maximum: ~5 meters depending on environment.

**Q: Does it work offline?**
A: Porcupine wake word detection works offline. Silero VAD works offline. Only MQTT requires network.

**Q: Can I use a different STT/TTS service?**
A: Yes! The service only publishes MQTT messages. Subscribe to them with any service.

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
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:
- **This service**: [Open an issue](https://github.com/pandosme/axis-speaker-wakeword/issues)
- **Voice ACAP**: Visit https://github.com/pandosme/Voice
- **Axis devices**: [Axis Developer Community](https://www.axis.com/developer-community)
- **Porcupine**: [Picovoice Console](https://console.picovoice.ai/)

## Changelog

### v1.0.0 (2025-12-30)
- Initial release
- Multi-device support
- Conda environment management
- Interactive setup wizard
- Configurable VAD timing
- MQTT authentication support
```

## INSTALL.md

```markdown
# Installation Guide

Complete installation guide for Axis Speaker Wakeword Monitor.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Installation](#quick-installation)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Running as Service](#running-as-service)

## Prerequisites

### Required Software

- **Conda** (Miniconda or Anaconda)
- **FFmpeg**
- **Git**

### Required Hardware

- Axis network speaker or audio bridge
- MQTT broker
- Server/computer to run the service

### Network Requirements

- Network connectivity to Axis devices
- Network connectivity to MQTT broker
- Internet access for initial setup (downloading dependencies)

## Quick Installation

```
# 1. Clone repository
git clone https://github.com/pandosme/axis-speaker-wakeword.git
cd axis-speaker-wakeword

# 2. Run installation script
bash install.sh

# 3. Activate environment
conda activate wakeword

# 4. Run setup wizard
python setup.py

# 5. Test run
python app.py
```

## Manual Installation

### Step 1: Install Conda

**Linux (Ubuntu/Debian):**
```
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install
bash Miniconda3-latest-Linux-x86_64.sh -b

# Initialize
~/miniconda3/bin/conda init bash
source ~/.bashrc

# Verify
conda --version
```

**macOS:**
```
# Using Homebrew
brew install miniconda

# Initialize
conda init "$(basename "${SHELL}")"

# Restart terminal, then verify
conda --version
```

**Windows:**
1. Download from: https://docs.conda.io/en/latest/miniconda.html
2. Run installer
3. Open "Anaconda Prompt" or "Miniconda Prompt"

### Step 2: Install FFmpeg

**Linux (Ubuntu/Debian):**
```
sudo apt update
sudo apt install ffmpeg -y
ffmpeg -version
```

**macOS:**
```
brew install ffmpeg
ffmpeg -version
```

**Windows:**
1. Download from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH

### Step 3: Clone Repository

```
cd ~
git clone https://github.com/pandosme/axis-speaker-wakeword.git
cd axis-speaker-wakeword
```

### Step 4: Create Conda Environment

```
# Create environment from specification
conda env create -f environment.yml

# Activate environment
conda activate wakeword

# Verify Python version
python --version  # Should be 3.10.x
```

### Step 5: Verify Installation

```
# Check installed packages
conda list

# Should see:
# - python 3.10.x
# - numpy
# - pytorch
# - paho-mqtt
# - pvporcupine
# - etc.
```

## Configuration

### Option 1: Interactive Setup (Recommended)

```
conda activate wakeword
python setup.py
```

Follow the prompts to configure:
- Axis device credentials
- Device addresses
- MQTT broker details
- Porcupine API key

### Option 2: Manual Configuration

**Create .env file:**
```
cp .env.example .env
nano .env
```

Edit with your values:
```
AXIS_USERNAME=root
AXIS_PASSWORD=your_password
MQTT_BROKER=192.168.1.80
MQTT_PORT=1883
MQTT_USERNAME=mqtt_user  # Optional
MQTT_PASSWORD=mqtt_pass  # Optional
PORCUPINE_ACCESS_KEY=your_key_here
```

**Create config.yaml:**
```
cp config.yaml.example config.yaml
nano config.yaml
```

Edit device configuration:
```
axis:
  devices:
    - name: "Office"
      id: "office"
      address: "http://192.168.1.100"
      audio_source: 0
```

### Getting Porcupine API Key

1. Visit: https://console.picovoice.ai/
2. Sign up or log in
3. Click "Access Keys" in left sidebar
4. Click "Create new access key"
5. Name it (e.g., "axis-wakeword")
6. Copy the key
7. Paste into `.env` file

**Free tier includes:**
- 3 wake words
- Unlimited devices
- Unlimited API calls

## Testing

### Test 1: Configuration Files

```
# Verify files exist
ls -la .env config.yaml

# Check syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### Test 2: Dependencies

```
conda activate wakeword

# Test imports
python -c "import pvporcupine; import torch; import paho.mqtt.client; print('OK')"
```

### Test 3: RTSP Connection

```
# Test with FFplay (if available)
ffplay rtsp://USERNAME:PASSWORD@DEVICE_IP/axis-media/media.amp?audio=1

# Or test with FFmpeg
ffmpeg -i rtsp://USERNAME:PASSWORD@DEVICE_IP/axis-media/media.amp?audio=1 -t 5 test.wav
```

### Test 4: MQTT Connection

```
# Subscribe to test
mosquitto_sub -h MQTT_BROKER_IP -t 'test' -v

# In another terminal, publish
mosquitto_pub -h MQTT_BROKER_IP -t 'test' -m 'hello'
```

### Test 5: Run Application

```
conda activate wakeword
python app.py
```

**Expected output:**
```
============================================================
Multi-Device Wakeword Monitor
============================================================
✓ Loaded config.yaml
  Found 1 device(s) configured
✓ MQTT connected to 192.168.1.80:1883
...
```

**Test wake word:**
1. Say the wake word ("Porcupine" by default)
2. You should see: `📢 WAKEWORD DETECTED!`
3. Speak for a few seconds
4. Pause - you should see: `🔇 SILENCE DETECTED!`

## Running as Service

### Systemd (Linux)

**Find conda path:**
```
conda info --base
# Output: /home/username/miniconda3

# Environment path
ls ~/miniconda3/envs/wakeword/bin/python
```

**Create service file:**
```
sudo nano /etc/systemd/system/axis-wakeword.service
```

**Service configuration:**
```
[Unit]
Description=Axis Wakeword Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/axis-speaker-wakeword
Environment="PATH=/home/YOUR_USERNAME/miniconda3/envs/wakeword/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/YOUR_USERNAME/miniconda3/envs/wakeword/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `YOUR_USERNAME` with your actual username
- Conda path if different

**Enable and start:**
```
sudo systemctl daemon-reload
sudo systemctl enable axis-wakeword
sudo systemctl start axis-wakeword
```

**Check status:**
```
sudo systemctl status axis-wakeword
```

**View logs:**
```
# Follow logs
sudo journalctl -u axis-wakeword -f

# Last 100 lines
sudo journalctl -u axis-wakeword -n 100
```

**Restart service:**
```
sudo systemctl restart axis-wakeword
```

**Stop service:**
```
sudo systemctl stop axis-wakeword
```

## Updating

### Update Code

```
cd ~/axis-speaker-wakeword
git pull origin main
```

### Update Dependencies

```
conda activate wakeword
conda env update -f environment.yml --prune
```

### Restart Service

```
# If running as systemd service
sudo systemctl restart axis-wakeword

# Or manually
conda activate wakeword
python app.py
```

## Uninstallation

```
# Stop service (if running)
sudo systemctl stop axis-wakeword
sudo systemctl disable axis-wakeword
sudo rm /etc/systemd/system/axis-wakeword.service

# Remove conda environment
conda deactivate
conda env remove -n wakeword

# Remove code
rm -rf ~/axis-speaker-wakeword
```

## Multiple Servers

To install on multiple servers:

```
# On each server
git clone https://github.com/pandosme/axis-speaker-wakeword.git
cd axis-speaker-wakeword
bash install.sh
conda activate wakeword

# Configure different devices on each server
python setup.py

# Or copy configuration from first server
scp .env config.yaml user@other-server:~/axis-speaker-wakeword/
```

## Troubleshooting Installation

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

**Common issues:**

1. **Conda not found**
   - Restart terminal after conda installation
   - Run `conda init bash` and restart

2. **FFmpeg not found**
   - Install via package manager
   - Add to PATH

3. **Permission denied on install.sh**
   - Run: `chmod +x install.sh`

4. **Torch installation slow**
   - Be patient, it's a large package (500MB+)
   - Ensure stable internet connection

5. **Import errors**
   - Verify conda environment is activated
   - Run: `conda env create -f environment.yml` again
```

## TROUBLESHOOTING.md

```markdown
# Troubleshooting Guide

Common issues and solutions for Axis Speaker Wakeword Monitor.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Connection Issues](#connection-issues)
4. [Detection Issues](#detection-issues)
5. [Performance Issues](#performance-issues)
6. [Service Issues](#service-issues)

## Installation Issues

### Conda Not Found

**Problem:** `conda: command not found`

**Solution:**
```
# Restart terminal after conda installation
source ~/.bashrc

# Or manually initialize
~/miniconda3/bin/conda init bash
source ~/.bashrc

# Verify
conda --version
```

### FFmpeg Not Found

**Problem:** `ffmpeg: command not found`

**Solution:**
```
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify
which ffmpeg
ffmpeg -version
```

### Permission Denied on install.sh

**Problem:** `bash: ./install.sh: Permission denied`

**Solution:**
```
chmod +x install.sh
bash install.sh
```

### Torch Installation Fails or Hangs

**Problem:** Torch installation takes very long or fails

**Solution:**
```
# Cancel and install torch separately with conda
conda activate wakeword
conda install pytorch torchaudio -c pytorch

# Then install rest
pip install python-dotenv pyyaml paho-mqtt pvporcupine requests
```

### Wrong Python Version

**Problem:** Python 3.12 instead of 3.10

**Solution:**
```
# Remove environment
conda env remove -n wakeword

# Create with specific Python version
conda create -n wakeword python=3.10 -y
conda activate wakeword

# Install dependencies
conda env update -f environment.yml
```

## Configuration Issues

### Config File Not Found

**Problem:** `❌ config.yaml not found`

**Solution:**
```
# Copy from template
cp config.yaml.example config.yaml

# Edit with your settings
nano config.yaml

# Or run setup wizard
python setup.py
```

### Invalid YAML Syntax

**Problem:** `yaml.scanner.ScannerError`

**Solution:**
```
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Common issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing quotes around values with special characters
# - Missing colons after keys
```

### Porcupine Key Invalid

**Problem:** `❌ Porcupine failed: Invalid access key`

**Solution:**
1. Verify key in `.env` has no extra spaces
2. Generate new key at https://console.picovoice.ai/
3. Check account is active (free tier doesn't expire)
4. Ensure no quotes around the key in `.env`

```
# WRONG
PORCUPINE_ACCESS_KEY="your_key_here"

# CORRECT
PORCUPINE_ACCESS_KEY=your_key_here
```

## Connection Issues

### RTSP Connection Failed

**Problem:** `❌ RTSP stream failed`

**Diagnosis:**
```
# Test RTSP connection manually
ffplay rtsp://USERNAME:PASSWORD@DEVICE_IP/axis-media/media.amp?audio=1

# Or save test file
ffmpeg -i rtsp://USERNAME:PASSWORD@DEVICE_IP/axis-media/media.amp?audio=1 -t 10 test.wav
```

**Solutions:**

1. **Check credentials:**
   ```
   # Test HTTP access
   curl -u USERNAME:PASSWORD http://DEVICE_IP/axis-cgi/basicdeviceinfo.cgi
   ```

2. **Check network connectivity:**
   ```
   ping DEVICE_IP
   telnet DEVICE_IP 554  # RTSP port
   ```

3. **Verify RTSP is enabled:**
   - Log into Axis device web interface
   - Go to System > Security > Users
   - Ensure RTSP is not disabled

4. **Check firewall:**
   ```
   # Allow RTSP (port 554)
   sudo ufw allow 554/tcp
   ```

5. **Try different URL format:**
   ```
   # In config.yaml, try:
   address: "http://192.168.1.100"  # Use IP instead of hostname
   ```

### MQTT Connection Failed

**Problem:** `❌ MQTT connection failed`

**Diagnosis:**
```
# Test MQTT broker
mosquitto_sub -h MQTT_BROKER_IP -t 'test' -v

# In another terminal
mosquitto_pub -h MQTT_BROKER_IP -t 'test' -m 'hello'
```

**Solutions:**

1. **Check broker is running:**
   ```
   # On MQTT broker server
   sudo systemctl status mosquitto
   
   # Start if stopped
   sudo systemctl start mosquitto
   ```

2. **Check network connectivity:**
   ```
   ping MQTT_BROKER_IP
   telnet MQTT_BROKER_IP 1883
   ```

3. **Check authentication:**
   ```
   # Test with credentials
   mosquitto_sub -h MQTT_BROKER_IP -u USERNAME -P PASSWORD -t 'test' -v
   ```

4. **Check firewall:**
   ```
   # On MQTT broker server
   sudo ufw allow 1883/tcp
   ```

5. **Verify broker configuration:**
   ```
   # On MQTT broker server
   sudo nano /etc/mosquitto/mosquitto.conf
   
   # Should have:
   listener 1883
   allow_anonymous true  # Or set up authentication
   ```

### Network Timeout

**Problem:** Connection times out

**Solutions:**

1. **Check network routing:**
   ```
   traceroute DEVICE_IP
   traceroute MQTT_BROKER_IP
   ```

2. **Check for VLANs:**
   - Ensure devices are on same network or routing is configured
   - Check VLAN tagging if applicable

3. **Disable VPN:**
   - VPN may block local network access
   - Try disabling VPN temporarily

## Detection Issues

### No Wake Word Detection

**Problem:** Say wake word but nothing happens

**Diagnosis:**
Check logs for audio processing:
```
[device_id] 🎧 Audio processing started - listening for wakeword...
```

**Solutions:**

1. **Check audio input:**
   ```
   # Test RTSP audio
   ffplay rtsp://USERNAME:PASSWORD@DEVICE_IP/axis-media/media.amp?audio=1
   # You should hear audio from the Axis microphone
   ```

2. **Increase sensitivity:**
   ```
   # In config.yaml
   wakeword:
     threshold: 0.7  # Try higher value (was 0.5)
   ```

3. **Try different wake word:**
   ```
   # In config.yaml
   wakeword:
     model: "jarvis"  # Or: alexa, hey_google, computer
   ```

4. **Check distance:**
   - Speak from 1-3 meters away
   - Too close or too far may affect detection

5. **Check environment:**
   - Reduce background noise
   - Avoid echo-prone rooms

6. **Verify microphone:**
   - Log into Axis device web interface
   - Go to Audio settings
   - Check microphone is enabled and working
   - Adjust microphone gain if needed

### False Wake Word Detections

**Problem:** Wake word triggers randomly

**Solutions:**

1. **Decrease sensitivity:**
   ```
   # In config.yaml
   wakeword:
     threshold: 0.3  # Try lower value (was 0.5)
   ```

2. **Change wake word:**
   - Some wake words are more prone to false positives
   - Try "computer" or "jarvis" instead of "porcupine"

3. **Reduce noise:**
   - Move device away from speakers/TV
   - Reduce background noise sources

### VAD Cuts Off Too Early

**Problem:** Recording stops before user finishes

**Solutions:**

1. **Increase minimum recording time:**
   ```
   # In config.yaml
   vad:
     min_recording_time_ms: 2500  # Was 1500
   ```

2. **Decrease VAD threshold:**
   ```
   # In config.yaml
   vad:
     threshold: 0.3  # Was 0.5
   ```

3. **Increase silence duration:**
   ```
   # In config.yaml
   vad:
     min_silence_duration_ms: 1200  # Was 800
   ```

### VAD Never Stops Recording

**Problem:** Recording hits max timeout every time

**Solutions:**

1. **Increase VAD threshold:**
   ```
   # In config.yaml
   vad:
     threshold: 0.7  # Was 0.5
   ```

2. **Check for noise:**
   - Background noise may be detected as speech
   - Reduce noise sources
   - Adjust Axis microphone gain

3. **Decrease silence duration:**
   ```
   # In config.yaml
   vad:
     min_silence_duration_ms: 600  # Was 800
   ```

## Performance Issues

### High CPU Usage

**Problem:** CPU usage >50%

**Solutions:**

1. **Check number of devices:**
   - Each device uses ~5-10% CPU
   - Reduce number of devices if needed

2. **Reduce VAD processing:**
   ```
   # In config.yaml
   vad:
     speech_pad_ms: 10  # Was 30
   ```

3. **Use GPU for VAD (if available):**
   ```
   # Edit app.py, in initialize_vad():
   self.vad_model, _ = torch.hub.load(
       repo_or_dir='snakers4/silero-vad',
       model='silero_vad',
       force_reload=False,
       verbose=False
   )
   self.vad_model = self.vad_model.cuda()  # Add this line
   ```

### High Memory Usage

**Problem:** Memory usage >500MB per device

**Solutions:**

1. **Reduce buffer size:**
   ```
   # Edit app.py, in DeviceMonitor.__init__():
   self.audio_buffer = deque(maxlen=500)  # Was 1000
   ```

2. **Restart service periodically:**
   ```
   # Add to systemd service file:
   RuntimeMaxSec=86400  # Restart every 24 hours
   ```

### Network Bandwidth Issues

**Problem:** High network usage

**Solutions:**

1. **Each device uses ~128 kbps**
   - This is normal for 16kHz audio
   - Cannot be reduced without affecting quality

2. **Use local network:**
   - Don't route RTSP over internet
   - Keep devices on same LAN as service

## Service Issues

### Service Won't Start

**Problem:** `systemctl start axis-wakeword` fails

**Diagnosis:**
```
# Check service status
sudo systemctl status axis-wakeword

# View logs
sudo journalctl -u axis-wakeword -n 50
```

**Solutions:**

1. **Check paths in service file:**
   ```
   # Verify paths exist
   ls /home/USERNAME/miniconda3/envs/wakeword/bin/python
   ls /home/USERNAME/axis-speaker-wakeword/app.py
   ```

2. **Check permissions:**
   ```
   # Service should run as your user
   ls -la ~/axis-speaker-wakeword
   # Files should be owned by your user
   ```

3. **Test manual run:**
   ```
   cd ~/axis-speaker-wakeword
   conda activate wakeword
   python app.py
   # If this works, service file is misconfigured
   ```

4. **Check conda path:**
   ```
   # Find conda base
   conda info --base
   
   # Update service file with correct path
   sudo nano /etc/systemd/system/axis-wakeword.service
   ```

### Service Crashes

**Problem:** Service stops unexpectedly

**Diagnosis:**
```
# View crash logs
sudo journalctl -u axis-wakeword | grep -A 20 "error\|exception\|traceback"
```

**Solutions:**

1. **Enable restart:**
   ```
   # In service file
   [Service]
   Restart=always
   RestartSec=10
   ```

2. **Check for specific errors:**
   - RTSP disconnection → Network issue
   - MQTT disconnection → Broker issue
   - Memory error → Reduce buffer sizes

3. **Add logging:**
   ```
   # In config.yaml
   service:
     log_level: "DEBUG"
   ```

### Can't Stop Service

**Problem:** Service doesn't respond to stop command

**Solution:**
```
# Force kill
sudo systemctl kill axis-wakeword

# Then start fresh
sudo systemctl start axis-wakeword
```

## Getting Help

If issues persist:

1. **Collect information:**
   ```
   # System info
   uname -a
   conda --version
   python --version
   ffmpeg -version
   
   # Service logs
   sudo journalctl -u axis-wakeword -n 200 > logs.txt
   
   # Configuration (remove sensitive data)
   cat config.yaml
   ```

2. **Open an issue:**
   - Go to: https://github.com/pandosme/axis-speaker-wakeword/issues
   - Include system info and logs
   - Describe steps to reproduce

3. **Community support:**
   - Axis Developer Community
   - Picovoice forums
   - MQTT community

## Debug Mode

Enable detailed logging:

```
# In config.yaml
service:
  log_level: "DEBUG"
```

Run manually to see all output:
```
conda activate wakeword
python app.py
```
