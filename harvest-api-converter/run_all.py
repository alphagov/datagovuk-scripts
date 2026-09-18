#!/usr/bin/env python3
"""Run datapress_to_dcat.py for all sources, retrying on failure or timeout."""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent

SOURCES = [
    (
        "https://data.london.gov.uk/api/v3/datasets/export.json",
        "output/london-dcat.json",
    ),
    (
        "https://datamillnorth.org/api/v3/datasets/export.json",
        "output/data-mill-north-dcat.json",
    ),
    (
        "https://dataworks.calderdale.gov.uk/api/v3/datasets/export.json",
        "output/calderdale-dcat.json",
    ),
    (
        "https://open.barnet.gov.uk/api/v3/datasets/export.json",
        "output/barnet-dcat.json",
    ),
]

MAX_RETRIES = 3
RETRY_DELAY = 30  # seconds between attempts
TIMEOUT = 120  # seconds per attempt before killing


def run_once(url, output_path, attempt):
    proc = subprocess.Popen(
        [
            sys.executable,
            str(HERE / "datapress_to_dcat.py"),
            url,
            str(HERE / output_path),
        ]
    )
    try:
        proc.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        print(f"  attempt {attempt}: timed out after {TIMEOUT}s", file=sys.stderr)
        return False
    return proc.returncode == 0


def main():
    failed = []
    for url, output_path in SOURCES:
        print(f"Processing {url}")
        for attempt in range(1, MAX_RETRIES + 1):
            if run_once(url, output_path, attempt):
                break
            if attempt < MAX_RETRIES:
                print(
                    f"  attempt {attempt} failed, retrying in {RETRY_DELAY}s...",
                    file=sys.stderr,
                )
                time.sleep(RETRY_DELAY)
        else:
            print(f"Failed after {MAX_RETRIES} attempts: {url}", file=sys.stderr)
            failed.append(url)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
