"""Shared configuration for the noise-checker project."""

import os

# Recording window (24-hour format, PST)
START_TIME = "21:56"
END_TIME = "21:58"

# Segment duration in seconds (1 hour)
SEGMENT_DURATION = 30

# Audio settings
SAMPLE_RATE = 44100
CHANNELS = 1
MP3_BITRATE = 32  # kbps

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "recordings")

# Timezone
TIMEZONE = "America/Vancouver"
