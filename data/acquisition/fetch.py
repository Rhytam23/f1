"""Data Acquisition CLI tool for RacePulse.

Usage:
    python -m data.acquisition.fetch --circuit silverstone --season 2023 --session R --driver VER
"""

from __future__ import annotations

import argparse
import sys
from data.loaders.fastf1_loader import load_fastf1_session_telemetry


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and cache real F1 telemetry for RacePulse.")
    parser.add_argument("--circuit", type=str, default="Silverstone", help="Circuit name (Silverstone, Suzuka, etc.)")
    parser.add_argument("--season", type=int, default=2023, help="F1 Season year (e.g. 2023, 2024)")
    parser.add_argument("--session", type=str, default="R", help="Session type ('R', 'Q', 'FP1', 'FP2', 'FP3')")
    parser.add_argument("--driver", type=str, default="VER", help="Driver code (e.g. VER, HAM, NOR)")
    parser.add_argument("--cache-dir", type=str, default="data/cache", help="Local cache directory")

    args = parser.parse_args()

    print(f"Fetching F1 telemetry for {args.circuit} {args.season} [{args.session}] Driver: #{args.driver}...")
    frames = load_fastf1_session_telemetry(
        season=args.season,
        circuit=args.circuit,
        session_type=args.session,
        driver=args.driver,
        cache_dir=args.cache_dir,
    )

    print(f"Successfully processed {len(frames)} telemetry frames into data cache!")
    if frames:
        print(f"Sample Frame 1: Lap {frames[0].lap}, Speed {frames[0].speed_kph} kph, Compound: {frames[0].tyre_compound}")


if __name__ == "__main__":
    main()
