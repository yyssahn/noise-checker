#!/usr/bin/env python3
"""Step 1: Scheduled Recording with Segmentation.

Records audio between START_TIME and END_TIME in SEGMENT_DURATION chunks.
Each segment is saved as an MP3 at 32kbps mono using SoX.
Files are named: YYYYMMDD_HHMM_NoiseLog.mp3
"""

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

from config import (
    CHANNELS,
    END_TIME,
    MP3_BITRATE,
    OUTPUT_DIR,
    SAMPLE_RATE,
    SEGMENT_DURATION,
    START_TIME,
)


def in_recording_window(now: datetime) -> bool:
    """Check if current time falls within the recording window.

    Handles overnight windows (e.g. 22:00 → 07:00).
    """
    start = now.replace(
        hour=int(START_TIME.split(":")[0]),
        minute=int(START_TIME.split(":")[1]),
        second=0, microsecond=0,
    )
    end = now.replace(
        hour=int(END_TIME.split(":")[0]),
        minute=int(END_TIME.split(":")[1]),
        second=0, microsecond=0,
    )

    if start > end:  # overnight window
        return now >= start or now < end
    return start <= now < end


def seconds_until_window_end(now: datetime) -> float:
    """Return seconds remaining until the recording window closes."""
    end = now.replace(
        hour=int(END_TIME.split(":")[0]),
        minute=int(END_TIME.split(":")[1]),
        second=0, microsecond=0,
    )
    if end <= now:
        end += timedelta(days=1)
    return (end - now).total_seconds()


def record_segment(output_path: str, duration: int) -> None:
    """Record a single MP3 segment via SoX."""
    cmd = [
        "rec",
        "-r", str(SAMPLE_RATE),
        "-c", str(CHANNELS),
        "-C", str(MP3_BITRATE),
        output_path,
        "trim", "0", str(duration),
    ]
    print(f"  Recording → {os.path.basename(output_path)} ({duration}s)")
    subprocess.run(cmd, check=True)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    now = datetime.now()
    if not in_recording_window(now):
        print(f"Outside recording window ({START_TIME}–{END_TIME}). Current time: {now:%H:%M}")
        print("Waiting for window to open…")

    # Wait until inside the recording window
    while not in_recording_window(datetime.now()):
        time.sleep(30)

    print(f"Recording window active. Saving segments to: {OUTPUT_DIR}")

    while in_recording_window(datetime.now()):
        now = datetime.now()
        remaining = seconds_until_window_end(now)
        duration = int(min(SEGMENT_DURATION, remaining))
        if duration <= 0:
            break

        filename = now.strftime("%Y%m%d_%H%M_NoiseLog.mp3")
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            record_segment(filepath, duration)
        except FileNotFoundError:
            sys.exit("Error: SoX is not installed. Install with: brew install sox  (or)  sudo apt install sox libsox-fmt-mp3")
        except subprocess.CalledProcessError as exc:
            print(f"  ⚠ Segment failed: {exc}", file=sys.stderr)
            time.sleep(5)
            continue

    print("Recording window closed. Session complete.")


if __name__ == "__main__":
    main()
