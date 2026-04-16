# Noise Checker

Automated overnight noise monitoring system. Records audio in scheduled windows, analyzes decibel levels, and produces daily CSV logs.

## Prerequisites

- Python 3.10+
- [SoX](https://sox.sourceforge.net/) with MP3 support

```bash
# macOS
brew install sox

# Raspberry Pi / Debian
sudo apt install sox libsox-fmt-all
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

**Verify your microphone works:**
```bash
python main.py --verify
```

**Start recording (waits for the configured time window):**
```bash
python main.py
```

## Configuration

Edit `src/noise_checker/config.py`:

| Setting | Default | Description |
|---|---|---|
| `START_TIME` | `22:00` | Recording window start (24h) |
| `END_TIME` | `07:00` | Recording window end (24h) |
| `SEGMENT_DURATION` | `3600` | Seconds per audio segment |
| `CALIBRATION_OFFSET` | `30.0` | dB offset so silence ≈ 30 dB |
| `DB_THRESHOLD` | `60.0` | Threshold for "loud" events |
| `ANALYSIS_INTERVAL` | `5` | Seconds between dB samples |

## Output

- `recordings/` — MP3 segments named `YYYYMMDD_HHMM_NoiseLog.mp3`
- `logs/` — Daily CSV files named `YYYY-MM-DD_noise_log.csv`
