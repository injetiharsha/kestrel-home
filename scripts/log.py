#!/usr/bin/env python3
"""Logging helper for the Kestrel Home project.

Usage:
    python scripts/log.py note "Completed Phase P0 setup"
    python scripts/log.py ai   "Antigravity Claude, scaffold generation, helped"

Appends timestamped entries to notes/LOG.md.
"""

import sys
import datetime
import pathlib

LOG_FILE = pathlib.Path(__file__).resolve().parent.parent / "notes" / "LOG.md"


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/log.py <note|ai> \"<message>\"")
        sys.exit(1)

    kind = sys.argv[1].lower()
    message = " ".join(sys.argv[2:])

    if kind not in ("note", "ai"):
        print(f"Unknown log kind: {kind}. Use 'note' or 'ai'.")
        sys.exit(1)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag = "NOTE" if kind == "note" else "AI"
    entry = f"- [{tag}] {timestamp} — {message}\n"

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create file with header if it doesn't exist
    if not LOG_FILE.exists():
        LOG_FILE.write_text("# Project Log\n\n", encoding="utf-8")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Logged: {entry.strip()}")


if __name__ == "__main__":
    main()
