# Pi Buddy 🤖

An offline AI voice assistant running entirely on a Raspberry Pi 5. Speak to it, it thinks, it speaks back — no cloud, no subscriptions, zero cost to run.

## Demo
- 🎙 Speak → Whisper.cpp transcribes locally
- 🧠 Ollama + LLaMA 3.2 1B generates a response
- 🔊 Piper TTS speaks the reply through your headset

## Hardware
- Raspberry Pi 5 (8GB)
- Sabrent USB External Stereo Sound Adapter (AU-MMSA)
- Wired 3.5mm headset with mic (single TRRS plug + splitter)

## Stack
| Component | Tool |
|---|---|
| Speech to Text | whisper.cpp (base.en model) |
| LLM | Ollama + LLaMA 3.2 1B |
| Text to Speech | Piper TTS (en_US lessac medium) |
| Voice Detection | webrtcvad |

## Setup

### 1. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b
```

### 2. Build Whisper.cpp
```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
bash ./models/download-ggml-model.sh base.en
```

### 3. Install Piper TTS
```bash
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz
tar -xzf piper_linux_aarch64.tar.gz
sudo apt install -y libespeak-ng1
sudo ln -sf ~/piper/piper /usr/bin/piper

mkdir -p ~/piper-voices && cd ~/piper-voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### 4. Install Python dependencies
```bash
pip3 install requests webrtcvad-wheels setuptools --break-system-packages
```

### 5. Run
```bash
ollama serve &
python3 buddy.py
```

## Usage
- Just speak — silence detection auto-stops recording
- Say **"goodbye"** to exit cleanly

## Author
Michael Ferka — Computer Engineer | IoT & AI Developer
