#!/usr/bin/env python3
"""
Process a GitHub issue to update the SQLite database.

Parses the event payload for URLs and metadata, imports results via CLI,
recalculates rankings, and writes the DB to data/running.db.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("+", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(proc.stdout)
    return proc.returncode == 0


def extract_urls(text: str) -> list:
    if not text:
        return []
    url_re = re.compile(r'https?://[^\s)]+')
    return url_re.findall(text)


def label_value(labels, prefix):
    for lbl in labels:
        name = lbl.get('name', '')
        if name.lower().startswith(prefix):
            return name.split(':', 1)[-1].strip()
    return None


def guess_name_year(title: str, body: str) -> tuple:
    combined = f"{title} {body}" if body else title
    m = re.search(r'(19|20)\d{2}', combined)
    year = int(m.group(0)) if m else None
    # Remove year and common words
    name = re.sub(r'(19|20)\d{2}', '', title)
    name = re.sub(r'results?|race', '', name, flags=re.IGNORECASE).strip()
    return name or None, year


def main():
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    db_path = os.environ.get('DB_PATH', 'data/running.db')
    if not event_path or not os.path.exists(event_path):
        print("GITHUB_EVENT_PATH missing")
        sys.exit(0)

    with open(event_path, 'r') as f:
        event = json.load(f)

    issue = event.get('issue', {})
    title = issue.get('title', '')
    body = issue.get('body', '')
    labels = issue.get('labels', [])

    urls = extract_urls(body)
    race_label = label_value(labels, 'race:')
    year_label = label_value(labels, 'year:')
    category_label = label_value(labels, 'category:')
    default_cat_label = label_value(labels, 'default_cat:')

    name, year = guess_name_year(title, body)
    if race_label:
        name = race_label
    if year_label:
        try:
            year = int(year_label)
        except ValueError:
            pass

    category = category_label or 'road_race'
    default_age_category = default_cat_label or None

    # Ensure data directory exists
    Path('data').mkdir(parents=True, exist_ok=True)

    if not urls:
        print("No URLs found in issue body; nothing to import.")
        sys.exit(0)

    # Import each URL
    for u in urls:
        cmd = [
            'python', '-m', 'running_results.cli',
            '--db', db_path,
            'import-url', u,
            '--name', name or 'Unknown Race',
            '--year', str(year or 0),
            '--category', category,
        ]
        if default_age_category:
            cmd += ['--default-category', default_age_category]
        ok = run(cmd)
        if not ok:
            print(f"Failed to import {u}")

    # Recalculate rankings
    run(['python', '-m', 'running_results.cli', '--db', db_path, 'calculate-rankings', '--recalculate'])


if __name__ == '__main__':
    main()
