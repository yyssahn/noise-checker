#!/usr/bin/env python3
"""Step 0: Verify Microphone & Recording.

Records a 5-second WAV clip via SoX, then prints basic audio info
(sample rate, channels, duration) to confirm the mic is working.
"""

import subprocess
import sys
import tempfile
import os

from config import SAMPLE_RATE, CHANNELS


def record_test_clip(output_path: str, duration: int = 5) -> None:
    """Record a short WAV clip using SoX's rec command."""
    cmd = [
        "rec",
        "-r", str(SAMPLE_RATE),
        "-c", str(CHANNELS),
        output_path,
        "trim", "0", str(duration),
    ]
    print(f"Recording {duration}s clip → {output_path}")
    subprocess.run(cmd, check=True)


def get_audio_info(file_path: str) -> dict:
    """Return sample rate, channels, and duration via soxi."""
    result = subprocess.run(
        ["soxi", file_path], capture_output=True, text=True, check=True
    )
    info = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if "sample rate" in key:
            info["sample_rate"] = val
        elif "channels" in key:
            info["channels"] = val
        elif "duration" in key:
            info["duration"] = val
    return info


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        clip_path = os.path.join(tmpdir, "test_clip.wav")
        try:
            record_test_clip(clip_path)
        except FileNotFoundError:
            sys.exit("Error: SoX is not installed. Install with: brew install sox  (or)  sudo apt install sox")
        except subprocess.CalledProcessError as exc:
            sys.exit(f"Recording failed: {exc}")

        if not os.path.exists(clip_path) or os.path.getsize(clip_path) == 0:
            sys.exit("Error: recorded file is empty — check your microphone.")

        info = get_audio_info(clip_path)
        print("\n=== Audio Info ===")
        for k, v in info.items():
            print(f"  {k}: {v}")

        size_kb = os.path.getsize(clip_path) / 1024
        print(f"  file_size: {size_kb:.1f} KB")
        print("\n✅ Microphone verified — audio captured successfully.")


if __name__ == "__main__":
    main()
