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
    print_step("1/3", "Setting up environment variables (.env)")
    
    if os.path.exists('.env'):
        if not yes_no(".env file already exists. Overwrite?", default=False):
            print("   Skipping .env setup")
            return
    
    # Copy template
    if not os.path.exists('.env.example'):
        print("   ❌ Error: .env.example not found!")
        return
    
    shutil.copy('.env.example', '.env')
    print("   ✓ Created .env from template")
    
    # Get values from user
    print("\n   Configure environment variables:")
    print("   (Press Enter to keep example values)")
    
    axis_username = get_input("   Axis username", "root")
    axis_password = get_input("   Axis password", "")
    mqtt_broker = get_input("   MQTT broker IP/hostname", "192.168.1.80")
    mqtt_port = get_input("   MQTT port", "1883")
    
    print("\n   Porcupine Access Key:")
    print("   Get your key from: https://console.picovoice.ai/")
    porcupine_key = get_input("   Porcupine access key", "your-porcupine-access-key-here")
    
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
        f.write("\n\n")
        f.write("# ============================\n")
        f.write("# Porcupine Access Key\n")
        f.write("# ============================\n")
        f.write(f"PORCUPINE_ACCESS_KEY={porcupine_key}\n")
    
    print("   ✓ Saved configuration to .env")


def setup_config_file():
    """Create config.yaml from template"""
    print_step("2/3", "Setting up device configuration (config.yaml)")
    
    if os.path.exists('config.yaml'):
        if not yes_no("config.yaml already exists. Overwrite?", default=False):
            print("   Skipping config.yaml setup")
            return
    
    # Copy template
    if not os.path.exists('config.yaml.example'):
        print("   ❌ Error: config.yaml.example not found!")
        return
    
    shutil.copy('config.yaml.example', 'config.yaml')
    print("   ✓ Created config.yaml from template")
    
    if not yes_no("   Would you like to configure a device now?", default=True):
        print("   You can edit config.yaml manually later")
        return
    
    # Get device details
    print("\n   Configure first Axis device:")
    device_name = get_input("   Device name (e.g., 'Office')", "Office")
    device_id = get_input("   Device ID (e.g., 'ACCC8EF67F46')", "device001")
    device_address = get_input("   Device address (e.g., 'http://192.168.1.100')", "http://192.168.1.100")
    
    mqtt_broker = get_input("   MQTT broker IP", "192.168.1.80")
    
    # Read template
    with open('config.yaml.example', 'r') as f:
        config_content = f.read()
    
    # Simple replacements (basic approach)
    config_content = config_content.replace('name: "Kontoret"', f'name: "{device_name}"')
    config_content = config_content.replace('id: "ACCC8EF67F46"', f'id: "{device_id}"')
    config_content = config_content.replace('address: "http://speaker-kontoret.internal"', f'address: "{device_address}"')
    config_content = config_content.replace('broker: "192.168.0.57"', f'broker: "{mqtt_broker}"')
    
    # Write config
    with open('config.yaml', 'w') as f:
        f.write(config_content)
    
    print("   ✓ Saved configuration to config.yaml")


def check_dependencies():
    """Check if dependencies are installed"""
    print_step("3/3", "Checking dependencies")
    
    # Check FFmpeg
    if shutil.which('ffmpeg') is None:
        print("   ⚠️  FFmpeg not found in PATH")
        print("   Install FFmpeg:")
        print("      Ubuntu/Debian: sudo apt install ffmpeg")
        print("      macOS: brew install ffmpeg")
        print("      Windows: https://ffmpeg.org/download.html")
    else:
        print("   ✓ FFmpeg found")
    
    # Check Python packages
    try:
        import paho.mqtt.client
        print("   ✓ paho-mqtt installed")
    except ImportError:
        print("   ⚠️  paho-mqtt not installed")
        print("   Run: pip install -r requirements.txt")
        return
    
    try:
        import pvporcupine
        print("   ✓ pvporcupine installed")
    except ImportError:
        print("   ⚠️  pvporcupine not installed")
        print("   Run: pip install -r requirements.txt")
        return
    
    try:
        import torch
        print("   ✓ torch installed")
    except ImportError:
        print("   ⚠️  torch not installed")
        print("   Run: pip install -r requirements.txt")
        return
    
    print("\n   ✓ All dependencies installed!")


def main():
    """Main setup function"""
    print_header("Axis Speaker Wakeword Monitor - Setup")
    print("\nThis script will help you set up the required configuration files.")
    print("You'll need:")
    print("  • Axis device credentials (username/password)")
    print("  • MQTT broker IP address")
    print("  • Porcupine API key from https://console.picovoice.ai/")
    
    if not yes_no("\nReady to continue?", default=True):
        print("\nSetup cancelled.")
        sys.exit(0)
    
    # Run setup steps
    setup_env_file()
    setup_config_file()
    check_dependencies()
    
    # Final instructions
    print_header("Setup Complete!")
    print("\nNext steps:")
    print("  1. Review and edit .env if needed")
    print("  2. Review and edit config.yaml to add more devices")
    print("  3. Install dependencies (if not already done):")
    print("     pip install -r requirements.txt")
    print("  4. Run the service:")
    print("     python app.py")
    print("\nFor more information, see README.md")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
