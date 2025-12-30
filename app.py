"""
Multi-Device Wakeword Monitor for Axis Speakers
Supports multiple devices, each with their own MQTT topics based on device ID
"""

import sys
import time
import os
import threading
import queue
import struct
import subprocess
import numpy as np
from dotenv import load_dotenv
import yaml
import pvporcupine
import torch
import paho.mqtt.client as mqtt
from collections import deque


class DeviceMonitor:
    """Monitor for a single device"""
    def __init__(self, device_config, shared_config, porcupine_access_key):
        self.device_config = device_config
        self.shared_config = shared_config
        self.porcupine_access_key = porcupine_access_key
        
        # Device identification
        self.device_name = device_config['name']
        self.device_id = device_config['id']
        self.address = device_config['address'].replace('http://', '').replace('https://', '')
        self.audio_source = device_config.get('audio_source', 0)
        
        # Components
        self.mqtt_client = None
        self.porcupine = None
        self.vad_model = None
        self.ffmpeg_process = None
        self.audio_thread = None
        self.running = False
        self.audio_buffer = deque(maxlen=1000)
        self.buffer_lock = threading.Lock()
        
        # State tracking
        self.wakeword_detected = False
        self.recording_start_time = None
        self.silence_start_time = None
        
        # VAD timing from shared config
        vad_config = shared_config.get('vad', {})
        self.vad_threshold = vad_config.get('threshold', 0.5)
        self.min_recording_time = vad_config.get('min_recording_time_ms', 1500) / 1000.0
        self.min_silence_duration = vad_config.get('min_silence_duration_ms', 800) / 1000.0
        self.max_recording_time = vad_config.get('max_recording_time_ms', 7000) / 1000.0
        
        # MQTT topics (use device_id)
        mqtt_config = shared_config['mqtt']
        self.topics = {
            'wakeword': mqtt_config['topics']['wakeword'].replace('{device_id}', self.device_id),
            'vad_start': mqtt_config['topics']['vad_start'].replace('{device_id}', self.device_id),
            'vad_stop': mqtt_config['topics']['vad_stop'].replace('{device_id}', self.device_id),
            'status': mqtt_config['topics']['status'].replace('{device_id}', self.device_id),
        }
    
    def initialize(self, mqtt_client, vad_model):
        """Initialize device with shared resources"""
        self.mqtt_client = mqtt_client
        self.vad_model = vad_model
        
        print(f"\n{'='*60}")
        print(f"Initializing: {self.device_name} (ID: {self.device_id})")
        print(f"{'='*60}")
        
        # Initialize Porcupine for this device
        if not self.initialize_porcupine():
            return False
        
        # Start RTSP stream
        if not self.start_rtsp_stream():
            return False
        
        print(f"✓ {self.device_name} ready!")
        print(f"  MQTT topics:")
        print(f"    Wakeword: {self.topics['wakeword']}")
        print(f"    VAD Stop: {self.topics['vad_stop']}")
        
        return True
    
    def initialize_porcupine(self):
        """Initialize Porcupine wakeword detection"""
        try:
            wakeword_config = self.shared_config.get('wakeword', {})
            model = wakeword_config.get('model', 'porcupine')
            
            keyword_map = {
                'hey_mycroft': 'porcupine',
                'hey_jarvis': 'jarvis',
                'alexa': 'alexa',
                'hey_google': 'hey google',
                'porcupine': 'porcupine',
                'jarvis': 'jarvis',
                'computer': 'computer',
            }
            
            keyword = keyword_map.get(model, 'porcupine')
            sensitivity = wakeword_config.get('threshold', 0.5)
            
            self.porcupine = pvporcupine.create(
                access_key=self.porcupine_access_key,
                keywords=[keyword],
                sensitivities=[sensitivity]
            )
            print(f"  ✓ Porcupine: '{keyword}' (sensitivity: {sensitivity})")
            return True
        except Exception as e:
            print(f"  ❌ Porcupine failed: {e}")
            return False
    
    def start_rtsp_stream(self):
        """Start RTSP stream using FFmpeg"""
        try:
            username = os.getenv('AXIS_USERNAME', 'root')
            password = os.getenv('AXIS_PASSWORD', '')
            
            rtsp_url = f"rtsp://{username}:{password}@{self.address}/axis-media/media.amp?audio=1"
            
            cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', rtsp_url,
                '-ar', '16000',
                '-ac', '1',
                '-f', 's16le',
                'pipe:1'
            ]
            
            print(f"  🎤 Starting RTSP stream from {self.address}")
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=4096
            )
            
            time.sleep(1.5)
            
            print(f"  ✓ RTSP stream connected (16kHz mono PCM)")
            
            self.running = True
            self.audio_thread = threading.Thread(target=self._read_rtsp_loop, daemon=True)
            self.audio_thread.start()
            
            return True
            
        except Exception as e:
            print(f"  ❌ RTSP stream failed: {e}")
            return False
    
    def _read_rtsp_loop(self):
        """Continuously read audio from FFmpeg into buffer"""
        chunk_size = 3200
        
        while self.running:
            try:
                chunk = self.ffmpeg_process.stdout.read(chunk_size)
                if not chunk:
                    break
                
                with self.buffer_lock:
                    self.audio_buffer.append(chunk)
                    
            except Exception as e:
                print(f"[{self.device_id}] ⚠️ Stream read error: {e}")
                break
        
        print(f"[{self.device_id}] ⚠️ RTSP stream ended")
    
    def read_frame(self, frame_size):
        """Read audio frame from buffer"""
        with self.buffer_lock:
            if not self.audio_buffer:
                return None
            
            collected = b''
            chunks_to_remove = []
            
            for i, chunk in enumerate(self.audio_buffer):
                if len(collected) >= frame_size:
                    break
                collected += chunk
                chunks_to_remove.append(i)
            
            for i in reversed(chunks_to_remove):
                self.audio_buffer.popleft()
            
            if len(collected) >= frame_size:
                if len(collected) > frame_size:
                    remainder = collected[frame_size:]
                    self.audio_buffer.appendleft(remainder)
                return collected[:frame_size]
            else:
                if collected:
                    self.audio_buffer.appendleft(collected)
                return None
    
    def get_speech_probability(self, audio_samples):
        """Get speech probability using Silero VAD"""
        if len(audio_samples) < 512:
            return 0.0
        
        audio_float = audio_samples.astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_float[-512:])
        
        with torch.no_grad():
            speech_prob = self.vad_model(audio_tensor, 16000).item()
        
        return speech_prob
    
    def publish_wakeword_detected(self):
        """Publish MQTT message when wakeword is detected"""
        payload = "DETECTED"
        qos = self.shared_config['mqtt'].get('qos', 1)
        
        self.mqtt_client.publish(self.topics['wakeword'], payload, qos=qos)
        print(f"\n[{self.device_id}] 📢 WAKEWORD DETECTED! → {self.topics['wakeword']}")
    
    def publish_silence_detected(self, reason="silence"):
        """Publish MQTT message when VAD detects silence"""
        payload = "SILENCE"
        qos = self.shared_config['mqtt'].get('qos', 1)
        
        if self.recording_start_time:
            duration = time.time() - self.recording_start_time
            duration_str = f" ({duration:.1f}s)"
        else:
            duration_str = ""
        
        self.mqtt_client.publish(self.topics['vad_stop'], payload, qos=qos)
        
        if reason == "timeout":
            print(f"[{self.device_id}] 🔇 MAX TIME{duration_str}! → {self.topics['vad_stop']}")
        else:
            print(f"[{self.device_id}] 🔇 SILENCE{duration_str}! → {self.topics['vad_stop']}")
    
    def process_audio(self):
        """Process audio for wakeword and VAD detection"""
        frame_length = self.porcupine.frame_length
        frame_size_bytes = frame_length * 2
        
        vad_buffer = np.array([], dtype=np.int16)
        
        print(f"[{self.device_id}] 🎧 Audio processing started - listening for wakeword...")
        
        while self.running:
            try:
                audio_data = self.read_frame(frame_size_bytes)
                
                if not audio_data or len(audio_data) != frame_size_bytes:
                    time.sleep(0.01)
                    continue
                
                pcm = struct.unpack_from(f"{frame_length}h", audio_data)
                
                # Wakeword detection
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    self.publish_wakeword_detected()
                    self.wakeword_detected = True
                    self.recording_start_time = time.time()
                    self.silence_start_time = None
                    print(f"[{self.device_id}] 🎙️  Recording (min:{self.min_recording_time}s, max:{self.max_recording_time}s)")
                
                # VAD detection
                if self.wakeword_detected:
                    current_time = time.time()
                    recording_duration = current_time - self.recording_start_time
                    
                    # Check maximum time
                    if recording_duration >= self.max_recording_time:
                        self.publish_silence_detected(reason="timeout")
                        self.wakeword_detected = False
                        self.recording_start_time = None
                        self.silence_start_time = None
                        vad_buffer = np.array([], dtype=np.int16)
                        continue
                    
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    vad_buffer = np.concatenate([vad_buffer, audio_array])
                    
                    if len(vad_buffer) >= 512:
                        speech_prob = self.get_speech_probability(vad_buffer)
                        
                        if recording_duration >= self.min_recording_time:
                            if speech_prob > self.vad_threshold:
                                self.silence_start_time = None
                            else:
                                if self.silence_start_time is None:
                                    self.silence_start_time = current_time
                                
                                silence_duration = current_time - self.silence_start_time
                                
                                if silence_duration >= self.min_silence_duration:
                                    self.publish_silence_detected(reason="silence")
                                    self.wakeword_detected = False
                                    self.recording_start_time = None
                                    self.silence_start_time = None
                                    vad_buffer = np.array([], dtype=np.int16)
                        
                        vad_buffer = vad_buffer[-512:]
                                    
            except Exception as e:
                print(f"[{self.device_id}] ⚠️ Processing error: {e}")
                time.sleep(0.1)
    
    def shutdown(self):
        """Clean shutdown"""
        print(f"[{self.device_id}] Shutting down...")
        self.running = False
        
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=2)
            except:
                self.ffmpeg_process.kill()
        
        if self.porcupine:
            self.porcupine.delete()
        
        print(f"[{self.device_id}] ✓ Shutdown complete")


class MultiDeviceManager:
    """Manages multiple device monitors"""
    def __init__(self):
        self.config = None
        self.mqtt_client = None
        self.vad_model = None
        self.devices = []
        self.device_threads = []
    
    def load_config(self):
        """Load configuration"""
        load_dotenv()
        
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
            print("✓ Loaded config.yaml")
            
            device_count = len(self.config['axis']['devices'])
            print(f"  Found {device_count} device(s) configured")
            
            return True
        except FileNotFoundError:
            print("❌ config.yaml not found")
            return False
    
    def initialize_mqtt(self):
        """Initialize shared MQTT client"""
        mqtt_config = self.config['mqtt']
        broker = mqtt_config['broker']
        port = mqtt_config['port']
        client_id = mqtt_config.get('client_id_prefix', 'axis_audio_service')
        
        try:
            self.mqtt_client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id
            )
        except AttributeError:
            self.mqtt_client = mqtt.Client(client_id)
        
        try:
            self.mqtt_client.connect(broker, port, 60)
            self.mqtt_client.loop_start()
            print(f"✓ MQTT connected to {broker}:{port}")
            return True
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")
            return False
    
    def initialize_vad(self):
        """Initialize shared Silero VAD"""
        try:
            vad_config = self.config.get('vad', {})
            
            print("Loading Silero VAD (shared)...")
            self.vad_model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                verbose=False
            )
            print(f"✓ Silero VAD initialized")
            print(f"  Threshold: {vad_config.get('threshold', 0.5)}")
            print(f"  Min recording: {vad_config.get('min_recording_time_ms', 1500)}ms")
            print(f"  Silence duration: {vad_config.get('min_silence_duration_ms', 800)}ms")
            print(f"  Max recording: {vad_config.get('max_recording_time_ms', 7000)}ms")
            return True
        except Exception as e:
            print(f"❌ VAD initialization failed: {e}")
            return False
    
    def initialize_devices(self):
        """Initialize all device monitors"""
        access_key = os.getenv('PORCUPINE_ACCESS_KEY')
        
        if not access_key:
            print("❌ PORCUPINE_ACCESS_KEY not found in .env")
            return False
        
        for device_config in self.config['axis']['devices']:
            monitor = DeviceMonitor(device_config, self.config, access_key)
            
            if monitor.initialize(self.mqtt_client, self.vad_model):
                self.devices.append(monitor)
            else:
                print(f"❌ Failed to initialize {device_config['name']}")
        
        return len(self.devices) > 0
    
    def run(self):
        """Run all device monitors"""
        print("\n" + "="*60)
        print(f"Multi-Device Wakeword Monitor")
        print("="*60)
        
        if not self.load_config():
            return
        
        if not self.initialize_mqtt():
            return
        
        if not self.initialize_vad():
            return
        
        if not self.initialize_devices():
            print("❌ No devices initialized")
            return
        
        print("\n" + "="*60)
        print(f"✓ All systems ready - {len(self.devices)} device(s) active")
        print("="*60)
        print("Active devices:")
        for device in self.devices:
            print(f"  • {device.device_name} ({device.device_id}) @ {device.address}")
        print("\nPress Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Start processing threads for each device
        for device in self.devices:
            thread = threading.Thread(target=device.process_audio, daemon=True)
            thread.start()
            self.device_threads.append(thread)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown all devices"""
        for device in self.devices:
            device.shutdown()
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        print("\n✓ All devices stopped")


def main():
    manager = MultiDeviceManager()
    manager.run()


if __name__ == "__main__":
    main()
