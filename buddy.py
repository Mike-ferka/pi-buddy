import subprocess, requests, os, tempfile, sys, struct, wave
import webrtcvad

# ── Config ──────────────────────────────────────────────
AUDIO_CARD     = "plughw:2,0"
WHISPER_BIN    = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
WHISPER_MODEL  = os.path.expanduser("~/whisper.cpp/models/ggml-base.en.bin")
PIPER_MODEL    = os.path.expanduser("~/piper-voices/en_US-lessac-medium.onnx")
OLLAMA_URL     = "http://localhost:11434/api/chat"
MODEL          = "llama3.2:1b"
SYSTEM_PROMPT = (
    "You are a helpful assistant. Be concise — max 2 sentences. "
    "Never say 'Pi Buddy'. Never repeat what the user said. "
    "Answer directly and naturally."
    "Never say the same thing or idea more than once. "
)

# Voice activity detection settings
SAMPLE_RATE    = 16000
FRAME_MS       = 30        # webrtcvad works with 10/20/30ms frames
FRAME_BYTES    = int(SAMPLE_RATE * FRAME_MS / 1000) * 2
SILENCE_LIMIT  = 1.5       # seconds of silence before stopping
VAD_AGGRESSIVE = 2         # 0-3, higher = more aggressive
# ────────────────────────────────────────────────────────

def record_until_silence():
    """Record audio, stop automatically after silence."""
    vad = webrtcvad.Vad(VAD_AGGRESSIVE)
    wav = tempfile.mktemp(suffix=".wav")

    print("🎙  Listening... (speak now)")

    # Use arecord to stream audio, read chunks
    cmd = [
        "arecord", "-D", AUDIO_CARD,
        "-f", "S16_LE", "-r", str(SAMPLE_RATE),
        "-c", "1", "--buffer-size=512", "-t", "raw"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    frames = []
    silent_frames = 0
    speaking_started = False
    max_silent = int(SILENCE_LIMIT * 1000 / FRAME_MS)

    try:
        while True:
            frame = proc.stdout.read(FRAME_BYTES)
            if len(frame) < FRAME_BYTES:
                break

            is_speech = vad.is_speech(frame, SAMPLE_RATE)

            if is_speech:
                speaking_started = True
                silent_frames = 0
                frames.append(frame)
            elif speaking_started:
                silent_frames += 1
                frames.append(frame)
                if silent_frames > max_silent:
                    print("✅ Got it, processing...")
                    break
            # If not started speaking yet, keep waiting
    finally:
        proc.terminate()

    if not frames or not speaking_started:
        return ""

    # Save to wav file
    with wave.open(wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))

    return wav

def transcribe(wav):
    """Transcribe wav file with whisper.cpp"""
    result = subprocess.run([
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", wav,
        "--no-timestamps",
        "-otxt", "-of", wav
    ], capture_output=True, text=True)

    txt = wav + ".txt"
    text = ""
    if os.path.exists(txt):
        text = open(txt).read().strip()
        os.remove(txt)
    os.remove(wav)
    return text

def ask_llm(user_text, history):
    history.append({"role": "user", "content": user_text})
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    reply = r.json()["message"]["content"].strip()
    history.append({"role": "assistant", "content": reply})
    return reply, history

def speak(text):
    clean = text.replace('"', "'").replace('\n', ' ')
    cmd = (
        f'echo "{clean}" | /usr/local/bin/piper/piper --model {PIPER_MODEL} --output_raw 2>/dev/null | '
        f'aplay -D {AUDIO_CARD} -r 22050 -f S16_LE -c 1 2>/dev/null'
    )
    subprocess.run(cmd, shell=True)

GOODBYE_WORDS = ["goodbye", "bye", "exit", "quit", "shut down", "stop"]

def main():
    print("🤖 Assistant ready. Speak anytime. Say 'goodbye' to exit.\n")
    history = []
    while True:
        try:
            wav = record_until_silence()
            if not wav:
                continue
            text = transcribe(wav)
            if not text:
                continue
            print(f"You  : {text}")

            # Check for goodbye
            if any(word in text.lower() for word in GOODBYE_WORDS):
                speak("Goodbye!")
                print("Goodbye!")
                sys.exit(0)

            reply, history = ask_llm(text, history)
            print(f"Buddy: {reply}\n")
            speak(reply)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()
