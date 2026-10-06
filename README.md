# 🎙️ Nexus: Privacy-First, Zero-Latency Hybrid Voice Activator
> **Smart India Hackathon 2026 Submission** | Problem Statement: Low Latency and Efficient Voice Activator for Edge Devices

[![Platform](https://img.shields.io/badge/Platform-ESP32--S3-orange.svg)](https://www.espressif.com/)
[![Framework](https://img.shields.io/badge/Framework-ESP--IDF_v5.5-blue.svg)](https://docs.espressif.com/projects/esp-idf/)
[![ML](https://img.shields.io/badge/TinyML-TensorFlow_Lite_Micro-FF6F00.svg)](https://www.tensorflow.org/lite/microcontrollers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nexus** is an ultra-lightweight, hybrid edge-to-cloud voice activation system. It solves the critical privacy and cost issues of modern smart speakers by running a custom, locally-trained wake word engine ("Nexus") entirely offline. 

The device only streams audio to the cloud *after* the wake word is verified, using mathematical Voice Activity Detection (VAD) to dynamically cut the stream the moment the user stops speaking.

---

## 🏆 Proven Hardware Metrics
Benchmarked live on a physical **ESP32-S3** microcontroller:

| Metric | Target Constraint | Our Result | Proof of Engineering |
| :--- | :--- | :--- | :--- |
| **RAM Footprint** | `< 256 KB` | **~110 KB** | INT8 Quantized CNN + strict memory arena allocation. |
| **CPU Utilization** | `< 10% Idle` | **9.0%** | Inference completes in 1.5ms per 16.6ms hardware frame. |
| **LAN Latency** | Minimal | **44 ms** | First audio byte received by local Python server. |
| **Accuracy** | High TPR, 0 FPR | **98.4% TPR** | Evaluated on n=5000 with Hard Negative penalization. |

🎥 **[Click Here to Watch the Live Hardware Demo]**(https://youtu.be/VCu2WlZf8-4)

---

## 🚀 How to Run the Project (No ESPHome Required!)
To make evaluation easy for judges, we have extracted the raw **ESP-IDF C++ source code** and provided **pre-compiled `.bin` binaries**. You do not need to install ESPHome to evaluate or run this firmware.

### Option A: The 1-Click Flash (Fastest Evaluation)
You can flash the pre-compiled firmware directly to an ESP32-S3 using the official Espressif Python tool.
1. Download `firmware.bin` from the `Precompiled_Binaries` folder.
2. Install esptool: `pip install esptool`
3. Flash the board (Replace `COM3` with your USB port):
   ```bash
   esptool.py -p COM3 -b 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_freq 80m --flash_size 4MB 0x10000 firmware.bin
   ```

### Option B: Build from C++ Source (ESP-IDF)
For code review, the raw generated C++ architecture is located in the `Firmware_ESP-IDF` folder.
1. Install [ESP-IDF v5.5+](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/get-started/index.html).
2. Open the ESP-IDF terminal and navigate to the `Firmware_ESP-IDF` folder.
3. Build and flash the project:
   ```bash
   idf.py build flash monitor
   ```

---

## ☁️ Running the Cloud ASR Server
Once the ESP32 is powered on, start the local edge gateway server to catch the audio stream and execute the transcription.

1. Navigate to the `Cloud_ASR_Server` directory.
2. Install the lightweight dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Open `asr_server.py` and update `ESP32_IP_ADDRESS` to match your ESP32's IP.
4. Run the server:
   ```bash
   python asr_server.py
   ```

**To Trigger:** Say **"Nexus"**. The ESP32's blue LED will instantly illuminate. Say your command. Exactly 1.5 seconds after you stop speaking, the Python server's VAD will automatically kill the stream, turn off the LED, and print your transcribed text!

---

## 🧠 ML Training Architecture
Our Wake Word model ("Nexus") was trained from scratch, completely avoiding generic, closed-source SDKs (like Alexa or Google).
* **Dataset:** 80/10/10 Split (n=20,000+). Positive synthetic samples (Piper-TTS) combined with hard-negatives ("Texas", "Lexus") and background noise (Google AudioSet / MIT RIR Echoes).
* **Acoustic Features:** 40-bin Log-Mel Spectrograms extracted every 10ms.
* **Model:** Depthwise Separable CNN (DS-CNN).
* **Quantization:** INT8 Post-Training Quantization reduced the model to ~40KB while maintaining 98.4% accuracy.

*Built with ❤️ for Smart India Hackathon 2026 by Team Uragirimono*
```
