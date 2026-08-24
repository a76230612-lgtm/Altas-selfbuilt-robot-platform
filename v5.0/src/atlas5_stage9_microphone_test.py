import sounddevice as sd
from scipy.io.wavfile import write
from datetime import datetime
import os


# =====================================================
# Atlas 5.0 Stage 9
# Microphone Recording Test
#
# Purpose:
# - Test whether the computer microphone can record audio.
# - Save a WAV file.
# - This file does NOT connect to ESP32 yet.
# =====================================================

SAMPLE_RATE = 16000
DURATION_SECONDS = 4
OUTPUT_DIR = "atlas5_voice_records"


def make_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def list_audio_devices():
    print("\n========== Audio Devices ==========")
    devices = sd.query_devices()
    print(devices)
    print("===================================")


def record_audio():
    make_output_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"atlas5_mic_test_{timestamp}.wav")

    print()
    print("[INFO] Recording will start now.")
    print(f"[INFO] Please speak for {DURATION_SECONDS} seconds.")
    print("[INFO] Recording...")

    audio = sd.rec(
        int(DURATION_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(filename, SAMPLE_RATE, audio)

    print("[OK] Recording finished.")
    print(f"[OK] Saved audio file: {filename}")


def main():
    print("Atlas 5.0 Stage 9 - Microphone Recording Test")
    print("This test only checks microphone recording.")
    print("It does not control ESP32 yet.")

    list_audio_devices()

    input("\nPress Enter to record a 4-second test audio...")
    record_audio()


if __name__ == "__main__":
    main()