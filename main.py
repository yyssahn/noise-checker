#!/usr/bin/env python3
"""Noise Checker — entry point.

Usage:
    python main.py            # record session, then analyze
    python main.py --verify   # mic check only
    python main.py --analyze  # analyze today's recordings only
    python main.py --analyze 2026-04-15  # analyze a specific date
"""

import sys

from src.noise_checker import analyzer, recorder


def main() -> None:
    args = sys.argv[1:]

    if "--verify" in args:
        recorder.verify_mic()
        return

    if "--analyze" in args:
        date = args[args.index("--analyze") + 1] if len(args) > args.index("--analyze") + 1 else None
        analyzer.analyze_session(date)
        return

    # Default: record then analyze
    recorder.record_session()
    print("\nAnalyzing today's recordings…")
    analyzer.analyze_session()


if __name__ == "__main__":
    main()
