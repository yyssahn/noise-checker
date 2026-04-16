"""Audio recording via SoX — mic verification and scheduled segmented capture."""

import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta

from . import config


def _parse_time(t: str) -> tuple[int, int]:
    h, m = t.split(":")
    return int(h), int(m)


def in_recording_window(now: datetime) -> bool:
    """Check if *now* falls within the configured recording window."""
    sh, sm = _parse_time(config.START_TIME)
    eh, em = _parse_time(config.END_TIME)
    start = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
    end = now.replace(hour=eh, minute=em, second=0, microsecond=0)
    if start > end:  # overnight
        return now >= start or now < end
    return start <= now < end


def seconds_until_window_end(now: datetime) -> float:
    eh, em = _parse_time(config.END_TIME)
    end = now.replace(hour=eh, minute=em, second=0, microsecond=0)
    if end <= now:
        end += timedelta(days=1)
    return (end - now).total_seconds()


def _record(output_path: str, duration: int, fmt_args: list[str] | None = None) -> None:
    cmd = [
        "rec",
        "-r", str(config.SAMPLE_RATE),
        "-c", str(config.CHANNELS),
    ]
    if fmt_args:
        cmd.extend(fmt_args)
    cmd.extend([output_path, "trim", "0", str(duration)])
    subprocess.run(cmd, check=True)


def verify_mic() -> None:
    """Record a 5-second WAV clip and print audio info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        clip = os.path.join(tmpdir, "test.wav")
        try:
            print("Recording 5s test clip…")
            _record(clip, 5)
        except FileNotFoundError:
            sys.exit("Error: SoX not installed. Install: brew install sox")
        except subprocess.CalledProcessError as e:
            sys.exit(f"Recording failed: {e}")

        if not os.path.exists(clip) or os.path.getsize(clip) == 0:
            sys.exit("Error: empty recording — check your microphone.")

        result = subprocess.run(["soxi", clip], capture_output=True, text=True, check=True)
        print("\n=== Audio Info ===")
        for line in result.stdout.splitlines():
            if ":" in line:
                print(f"  {line.strip()}")
        print(f"  File size: {os.path.getsize(clip) / 1024:.1f} KB")
        print("\n✅ Microphone verified.")


def _rename_segments(base_path: str, start_time: datetime) -> None:
    """Rename SoX numbered segments to YYYYMMDD_HHMM_NoiseLog.mp3."""
    import glob
    # SoX creates files like: segment001.mp3, segment002.mp3, ...
    stem = os.path.splitext(base_path)[0]
    for path in sorted(glob.glob(f"{stem}*.mp3")):
        # Extract segment number from filename (e.g. segment001.mp3 → 0)
        name = os.path.splitext(os.path.basename(path))[0]
        num = int(name.replace(os.path.basename(stem), "")) - 1
        ts = start_time + timedelta(seconds=num * config.SEGMENT_DURATION)
        new_name = ts.strftime("%Y%m%d_%H%M_NoiseLog.mp3")
        new_path = os.path.join(os.path.dirname(path), new_name)
        os.rename(path, new_path)
        print(f"  {new_name}")


def record_session() -> None:
    """Record gapless MP3 segments within the configured time window.

    Uses SoX's trim/newfile/restart to split recording into segments
    without any gaps between them.
    """
    if not in_recording_window(datetime.now()):
        print(f"Outside window ({config.START_TIME}–{config.END_TIME}). Waiting…")
    while not in_recording_window(datetime.now()):
        time.sleep(30)

    now = datetime.now()
    total = int(seconds_until_window_end(now))
    seg = config.SEGMENT_DURATION
    date_dir = os.path.join(config.RECORDINGS_DIR, now.strftime("%Y-%m-%d"))
    os.makedirs(date_dir, exist_ok=True)
    base_path = os.path.join(date_dir, "segment.mp3")

    # Build: rec ... segment.mp3 trim 0 <seg> : newfile : restart
    cmd = [
        "rec",
        "-r", str(config.SAMPLE_RATE),
        "-c", str(config.CHANNELS),
        "-C", str(config.MP3_BITRATE),
        base_path,
        "trim", "0", str(min(seg, total)),
    ]
    # Add newfile+restart pairs for remaining segments
    remaining = total - seg
    while remaining > 0:
        cmd.extend([":", "newfile", ":", "trim", "0", str(min(seg, remaining))])
        remaining -= seg

    print(f"Recording {total}s in {(total + seg - 1) // seg} gapless segments…")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("Error: SoX not installed. Install: brew install sox libsox-fmt-mp3")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Recording failed: {e}")

    _rename_segments(base_path, now)
    print("Recording window closed.")
