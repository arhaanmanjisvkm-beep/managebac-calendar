#!/usr/bin/env python3
"""Fetch the ManageBac calendar feed and republish a filtered summatives-only .ics.

The raw feed URL contains an auth token, so it lives only in config.json
(gitignored) - never committed. The output .ics strips descriptions before
it's written, since those often contain teacher names and personal notes and
this file is meant to be pushed to a public repo for Google Calendar to poll.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from icalendar import Calendar, Event

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
RAW_PATH = ROOT / "raw.ics"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fetch_raw(feed_url: str) -> bytes:
    req = urllib.request.Request(feed_url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    RAW_PATH.write_bytes(data)
    return data


def matches_any(patterns, text):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def filter_events(cal: Calendar, keywords, exclude_keywords):
    kept, dropped = [], []
    for component in cal.walk("VEVENT"):
        summary = str(component.get("SUMMARY", ""))
        included = matches_any(keywords, summary) and not matches_any(exclude_keywords, summary)
        (kept if included else dropped).append((summary, component))
    return kept, dropped


def build_filtered_calendar(kept):
    out = Calendar()
    out.add("PRODID", "-//managebac-calendar//sync.py//EN")
    out.add("VERSION", "2.0")
    for summary, component in kept:
        ev = Event()
        ev.add("SUMMARY", summary.strip())
        ev.add("UID", str(component.get("UID")))
        if component.get("DTSTART"):
            ev.add("DTSTART", component.get("DTSTART").dt)
        if component.get("DTEND"):
            ev.add("DTEND", component.get("DTEND").dt)
        if component.get("LOCATION"):
            ev.add("LOCATION", str(component.get("LOCATION")))
        out.add_component(ev)
    return out


def main():
    dry_run = "--dry-run" in sys.argv
    config = load_config()

    raw_bytes = fetch_raw(config["feed_url"])
    cal = Calendar.from_ical(raw_bytes)

    kept, dropped = filter_events(cal, config["keywords"], config["exclude_keywords"])

    print(f"Matched {len(kept)} summative/major events, dropped {len(dropped)} routine events.\n")
    print("KEPT:")
    for summary, component in sorted(kept, key=lambda kc: str(kc[1].get("DTSTART").dt)):
        dt = component.get("DTSTART").dt
        print(f"  {dt:%Y-%m-%d %H:%M}  {summary.strip()}")

    if dry_run:
        print("\n(dry run - nothing written)")
        return

    output_path = ROOT / config["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_cal = build_filtered_calendar(kept)
    output_path.write_bytes(filtered_cal.to_ical())
    print(f"\nWrote {len(kept)} events to {output_path}")


if __name__ == "__main__":
    main()
