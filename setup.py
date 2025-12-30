#!/usr/bin/env python3
"""
Interactive setup script for Axis Speaker Wakeword Monitor
Helps users configure .env and config.yaml files
"""

import os
import sys
import shutil
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(step, text):
    """Print a step indicator"""
    print(f"\n[{step}] {text}")


def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def yes_no(prompt, default=True):
    """Ask a yes/no question"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ['y', 'yes']


def setup_env_file():
    """Create .env file from template"""
    print_step("1/2", "Setting up environment variables (.env)")
    
    if os.path.exists('.env'):
        if not yes_no(".env file already exists. Overwrite?", default=False):
            print("   Skipping .env setup")
            return
    
    # Copy template
    if not os.path.exists('.env.example'):
        print("   ❌ Error: .env.example not found!")
        return
    
    print("\n   Configure environment variables:")
    print("   (Press Enter to use default values shown in brackets)")
    
    # Axis credentials
    print("\n   Axis Device Credentials:")
    axis_username = get_input("   Axis username", "root")
    axis_password = get_input("   Axis password")
    
    # MQTT configuration
    print("\n   MQTT Broker Configuration:")
    mqtt_broker = get_input("   MQTT broker hostname/IP", "192.168.1.80")
    mqtt_port = get_input("   MQTT port", "1883")
    
    mqtt_username = ""
    mqtt_password = ""
    if yes_no("   Does MQTT broker require authentication?", default=False):
        mqtt_username = get_input("   MQTT username")
        mqtt_password = get_input("   MQTT password")
    
    # Porcupine key
    print("\n   Porcupine Wake Word Detection:")
    print("   Get your FREE access key from: https://console.picovoice.ai/")
    print("   (Free tier: 3 wake words, unlimited devices)")
    porcupine_key = get_input("   Porcupine access key")
    
    # Write to .env
    with open('.env', 'w') as f:
        f.write("# ============================\n")
        f.write("# Axis Device Credentials\n")
        f.write("# ============================\n")
        f.write(f"AXIS_USERNAME={axis_username}\n")
        f.write(f"AXIS_PASSWORD={axis_password}\n")
        f.write("\n\n")
        f.write("# ============================\n")
        f.write("# MQTT Broker\n")
        f.write("# ============================\n")
        f.write(f"MQTT_BROKER={mqtt_broker}\n")
        f.write(f"MQTT_PORT={mqtt_port}\n")
        if mqtt_username:
            f.write(f"MQTT_USERNAME={mqtt_username}\n")
            f.write(f"MQTT_PASSWORD={mqtt_password}\n")
        f.write("\n\n")
        f.write("# ============================\n")
        f.write("# Porcupine Access Key\n")
        f.write("# ============================\n")
        f.write(f"PORCUPINE_ACCESS_KEY={porcupine_key}\n")
    
    print("   ✓ Saved configuration to .env")


def setup_config_file():
    """Create config.yaml from template"""
    print_step("2/2", "Setting up device configuration (config.yaml)")
    
    if os.path.exists('config.yaml'):
        if not yes_no("config.yaml already exists. Overwrite?", default=False):
            print("   Skipping config.yaml setup")
            return
    
    # Copy template
    if not os.path.exists('config.yaml.example'):
        print("   ❌ Error: config.yaml.example not found!")
        return
    
    # Read template
    with open('config.yaml.example', 'r') as f:
        config_lines = f.readlines()
    
    if not yes_no("   Would you like to configure your first Axis device now?", default=True):
        # Just copy template as-is
        shutil.copy('config.yaml.example', 'config.yaml')
        print("   ✓ Created config.yaml from template")
        print("   📝 Edit config.yaml manually to add your devices")
        return
    
    # Get device details
    print("\n   Configure first Axis device:")
    device_name = get_input("   Device name (e.g., 'Office', 'Kitchen')", "Office")
    device_id = get_input("   Device ID (lowercase, no spaces, e.g., 'office', 'ACCC8E123456')", "office")
    device_address = get_input("   Device address (e.g., 'http://192.168.1.100' or 'http://speaker.local')", "http://192.168.1.100")
    
    # Get MQTT broker (use same as .env)
    mqtt_broker = get_input("   MQTT broker IP/hostname", "192.168.1.80")
    
    # Process config template
    new_config = []
    for line in config_lines:
        # Replace first device configuration
        if 'name: "Kontoret"' in line:
            new_config.append(f'    - name: "{device_name}"\n')
        elif 'id: "ACCC8EF67F46"' in line:
            new_config.append(f'      id: "{device_id}"\n')
        elif 'address: "http://speaker-kontoret.internal"' in line:
            new_config.append(f'      address: "{device_address}"\n')
        elif 'broker: "192.168.0.57"' in line:
            new_config.append(f'  broker: "{mqtt_broker}"\n')
        else:
            new_config.append(line)
    
    # Write config
    with open('config.yaml', 'w') as f:
        f.writelines(new_config)
    
    print("   ✓ Saved configuration to config.yaml")
    print("   📝 To add more devices, edit config.yaml manually")


def check_dependencies():
    """Check if dependencies are installed"""
    print_header("Checking Dependencies")
    
    all_good = True
    
    # Check FFmpeg
    if shutil.which('ffmpeg') is None:
        print("   ⚠️  FFmpeg not found in PATH")
        print("   Install FFmpeg:")
        print("      Ubuntu/Debian: sudo apt install ffmpeg")
        print("      macOS: brew install ffmpeg")
        print("      Windows: https://ffmpeg.org/download.html")
        all_good = False
    else:
        print("   ✓ FFmpeg found")
    
    # Check Python environment
    in_conda = os.path.exists(os.path.join(sys.prefix, 'conda-meta'))
    if in_conda or 'CONDA_DEFAULT_ENV' in os.environ:
        env_name = os.environ.get('CONDA_DEFAULT_ENV', 'unknown')
        print(f"   ✓ Running in conda environment: {env_name}")
    elif hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"   ✓ Running in virtual environment")
    else:
        print("   ⚠️  Not running in virtual environment")
        print("   Recommended: conda create -n wakeword python=3.10")
        all_good = False
    
    # Check Python packages
    try:
        import dotenv
        print("   ✓ python-dotenv installed")
    except ImportError:
        print("   ⚠️  python-dotenv not installed")
        all_good = False
    
    try:
        import paho.mqtt.client
        print("   ✓ paho-mqtt installed")
    except ImportError:
        print("   ⚠️  paho-mqtt not installed")
        all_good = False
    
    try:
        import pvporcupine
        print("   ✓ pvporcupine installed")
    except ImportError:
        print("   ⚠️  pvporcupine not installed")
        all_good = False
    
    try:
        import torch
        print("   ✓ torch installed")
    except ImportError:
        print("   ⚠️  torch not installed")
        all_good = False
    
    if not all_good:
        print("\n   📦 Install missing dependencies:")
        print("      pip install -r requirements.txt")
    else:
        print("\n   ✓ All dependencies installed!")
    
    return all_good


def main():
    """Main setup function"""
    print_header("Axis Speaker Wakeword Monitor - Setup")
    print("\nThis script will help you set up the required configuration files.")
    print("\nYou'll need:")
    print("  • Axis device credentials (username/password)")
    print("  • Axis device IP address or hostname")
    print("  • MQTT broker IP/hostname (and credentials if required)")
    print("  • Porcupine API key from https://console.picovoice.ai/")
    
    if not yes_no("\nReady to continue?", default=True):
        print("\nSetup cancelled.")
        sys.exit(0)
    
    # Run setup steps
    setup_env_file()
    setup_config_file()
    deps_ok = check_dependencies()
    
    # Final instructions
    print_header("Setup Complete!")
    print("\n✓ Configuration files created:")
    if os.path.exists('.env'):
        print("   • .env (credentials)")
    if os.path.exists('config.yaml'):
        print("   • config.yaml (device configuration)")
    
    print("\nNext steps:")
    if not deps_ok:
        print("  1. Install dependencies:")
        print("     pip install -r requirements.txt")
        print("  2. Run the service:")
    else:
        print("  1. Run the service:")
    print("     python app.py")
    
    print("\n📖 For more information:")
    print("   • README.md - Full documentation")
    print("   • config.yaml - Add more devices")
    print("   • .env - Update credentials")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
