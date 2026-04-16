"""Step 2: Decibel analysis and CSV logging.

Reads recorded MP3 segments, computes RMS dB at configured intervals,
and writes a daily CSV with Timestamp, Avg_dB, Peak_dB, File_Reference
plus a summary row.
"""

import csv
import os
import subprocess
from datetime import datetime, timedelta

import numpy as np

from . import config


def _mp3_to_raw(mp3_path: str) -> np.ndarray:
    """Decode MP3 to raw 16-bit PCM samples via SoX."""
    result = subprocess.run(
        [
            "sox", mp3_path,
            "-t", "raw", "-r", str(config.SAMPLE_RATE),
            "-e", "signed", "-b", "16", "-c", "1",
            "-",
        ],
        capture_output=True, check=True,
    )
    return np.frombuffer(result.stdout, dtype=np.int16).astype(np.float64)


def _rms_db(samples: np.ndarray) -> float:
    """Compute RMS in dB (relative to int16 max) + calibration offset."""
    if len(samples) == 0:
        return config.CALIBRATION_OFFSET
    rms = np.sqrt(np.mean(samples ** 2))
    if rms < 1:
        return config.CALIBRATION_OFFSET
    db = 20 * np.log10(rms / 32768.0) + config.CALIBRATION_OFFSET + 96
    # +96 shifts full-scale 0 dBFS → ~96 dB SPL; silence → ~30 dB
    return round(db, 1)


def analyze_file(mp3_path: str) -> list[dict]:
    """Analyze a single MP3 file, returning per-interval dB rows."""
    samples = _mp3_to_raw(mp3_path)
    chunk_size = config.SAMPLE_RATE * config.ANALYSIS_INTERVAL
    filename = os.path.basename(mp3_path)

    # Parse start time from filename: YYYYMMDD_HHMM_NoiseLog.mp3
    try:
        ts = datetime.strptime(filename[:13], "%Y%m%d_%H%M")
    except ValueError:
        ts = datetime.now()

    rows = []
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i : i + chunk_size]
        if len(chunk) == 0:
            continue
        avg_db = _rms_db(chunk)
        if avg_db < config.LOG_MIN_DB:
            continue
        peak_amp = float(np.max(np.abs(chunk)))
        peak_db = round(20 * np.log10(max(peak_amp, 1) / 32768.0) + config.CALIBRATION_OFFSET + 96, 1)

        elapsed = timedelta(seconds=i // config.SAMPLE_RATE)
        rows.append({
            "Timestamp": (ts + elapsed).strftime("%Y-%m-%d %H:%M:%S"),
            "Avg_dB": avg_db,
            "Peak_dB": max(avg_db, peak_db),
            "File_Reference": filename,
        })

    return rows


def analyze_session(date_str: str | None = None) -> str:
    """Analyze all MP3s for a given date and write a daily CSV.

    Returns the path to the generated CSV.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    os.makedirs(config.LOGS_DIR, exist_ok=True)

    # Find matching MP3 files in the date subfolder
    date_dir = os.path.join(config.RECORDINGS_DIR, date_str)
    if not os.path.isdir(date_dir):
        print(f"No recordings found for {date_str}")
        return ""

    mp3_files = sorted(f for f in os.listdir(date_dir) if f.endswith(".mp3"))

    if not mp3_files:
        print(f"No recordings found for {date_str}")
        return ""

    all_rows: list[dict] = []
    for f in mp3_files:
        print(f"  Analyzing {f}…")
        all_rows.extend(analyze_file(os.path.join(date_dir, f)))

    # Write CSV
    csv_path = os.path.join(config.LOGS_DIR, f"{date_str}_noise_log.csv")
    fieldnames = ["Timestamp", "Avg_dB", "Peak_dB", "File_Reference"]

    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

        # Summary row
        if all_rows:
            avg_vals = [r["Avg_dB"] for r in all_rows]
            peak_vals = [r["Peak_dB"] for r in all_rows]
            above = sum(1 for v in avg_vals if v > config.DB_THRESHOLD)
            duration_above = above * config.ANALYSIS_INTERVAL
            writer.writerow({
                "Timestamp": "SUMMARY",
                "Avg_dB": round(max(avg_vals), 1),
                "Peak_dB": round(max(peak_vals), 1),
                "File_Reference": f"Above {config.DB_THRESHOLD}dB: {duration_above}s",
            })

    print(f"  CSV → {csv_path} ({len(all_rows)} samples)")
    return csv_path
