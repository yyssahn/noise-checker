"""Shared configuration for the noise-checker project."""

import os

# Recording window (24-hour format, local time)
START_TIME = "22:00"
END_TIME = "07:00"

# Segment duration in seconds (1 hour)
SEGMENT_DURATION = 3600

# Audio settings
SAMPLE_RATE = 44100
CHANNELS = 1
MP3_BITRATE = 32  # kbps

# Decibel analysis (Step 2)
CALIBRATION_OFFSET = 30.0  # dB offset so silence reads ~30 dB
DB_THRESHOLD = 60.0  # dB level considered "loud"
LOG_MIN_DB = 50.0  # only log samples above this level
ANALYSIS_INTERVAL = 5  # seconds between RMS samples

# Output directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
