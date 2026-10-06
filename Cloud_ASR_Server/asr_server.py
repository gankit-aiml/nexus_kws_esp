import asyncio
import time
import wave
import struct
import math
from aioesphomeapi import APIClient

# --- CONFIGURATION ---
ESP32_IP_ADDRESS = "10.189.133.171"  
PASSWORD = ""                        
OUTPUT_WAV = "keyword_recording.wav"

# --- VAD SETTINGS ---
VOLUME_THRESHOLD = 2500    
SILENCE_TIMEOUT = 2.0      
MAX_RECORD_TIME = 10.0     

def get_audio_volume(data):
    """Calculates the True AC Volume (Standard Deviation) to ignore INMP441 DC Offset"""
    data = data[:len(data) - (len(data) % 2)] 
    if not data: return 0
    count = len(data) // 2
    shorts = struct.unpack(f"<{count}h", data)
    mean = sum(shorts) / count
    sum_sq = sum((s - mean) ** 2 for s in shorts)
    return math.sqrt(sum_sq / count)

class CloudASRServer:
    def __init__(self):
        self.wav_file = None
        self.start_time = 0
        self.receiving_audio = False
        self.silence_start = 0
        self.packets_received = 0  # Tracks audio packets to filter out hardware pops!

    async def run(self):
        print(f"☁️ Cloud ASR Server Starting... Connecting to ESP32 at {ESP32_IP_ADDRESS}")
        
        cli = APIClient(ESP32_IP_ADDRESS, 6053, PASSWORD)
        await cli.connect(login=True)
        print("✅ Connected to Edge Device! Idling silently...\n")

        async def handle_start(*args, **kwargs):
            self.start_time = time.time()
            self.silence_start = time.time() 
            self.packets_received = 0  # Reset packet counter
            
            print("\n⚡ [EDGE TRIGGER] Wake Word 'Nexus' detected! Listening for your command...")
            
            self.wav_file = wave.open(OUTPUT_WAV, "wb")
            self.wav_file.setnchannels(1)
            self.wav_file.setsampwidth(2)
            self.wav_file.setframerate(16000)
            self.receiving_audio = True
            return 0  

        async def handle_audio(data, *args, **kwargs):
            if self.receiving_audio:
                raw_bytes = data if isinstance(data, bytes) else getattr(data, "data", b"")
                if not raw_bytes: return

                self.wav_file.writeframes(raw_bytes)
                self.packets_received += 1
                
                # Calculate latency on the very first audio packet
                if self.packets_received == 1:
                    latency = (time.time() - self.start_time) * 1000
                    print(f"⏱️  [LATENCY METRIC] First packet in {latency:.1f} ms")

                volume = get_audio_volume(raw_bytes)
                current_time = time.time()
                
                # --- POP FILTER: Ignore the first 5 packets (~0.2s) from the VAD ---
                if self.packets_received > 5:
                    if volume > VOLUME_THRESHOLD:
                        self.silence_start = current_time
                        print(f"🗣️ Speech Detected! (Vol: {volume:.0f})        ", end="\r")
                    else:
                        print(f"🤫 Silence...       (Vol: {volume:.0f})        ", end="\r")
                            
                stop_reason = None
                if (current_time - self.silence_start) > SILENCE_TIMEOUT:
                    stop_reason = f"\n🛑 [STREAM ENDED] Detected {SILENCE_TIMEOUT}s of silence."
                elif (current_time - self.start_time) > MAX_RECORD_TIME:
                    stop_reason = f"\n🛑 [STREAM ENDED] Hit maximum record limit of {MAX_RECORD_TIME}s."

                # STOP THE STREAM!
                if stop_reason:
                    self.receiving_audio = False
                    self.wav_file.close()
                    print(stop_reason)
                    print(f"💾 Audio saved to {OUTPUT_WAV}")
                    
                    try:
                        cli.send_voice_assistant_event(2, {})
                    except Exception as e:
                        print(f"Reset error: {e}")
                    
                    print("--------------------------------------------------")
                    print("☁️ Going back to sleep. Waiting for 'Nexus'...")

        async def handle_stop(*args, **kwargs):
            if self.receiving_audio:
                self.receiving_audio = False
                if self.wav_file:
                    self.wav_file.close()

        cli.subscribe_voice_assistant(
            handle_start=handle_start,
            handle_stop=handle_stop,
            handle_audio=handle_audio
        )
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await cli.disconnect()

if __name__ == "__main__":
    server = CloudASRServer()
    asyncio.run(server.run())