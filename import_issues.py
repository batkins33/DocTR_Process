import argparse
import csv
import os
import sys
import time

import requests

API = "https://api.github.com"


def open_csv_robust(path):
    """Try common encodings; fall back to replacing bad bytes."""
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return open(path, newline="", encoding=enc)
        except UnicodeDecodeError:
            continue
    return open(path, newline="", encoding="utf-8", errors="replace")


def safe_str(v):
    return (v or "").strip()


def parse_labels(raw):
    raw = safe_str(raw)
    if not raw:
        return []
    # allow semicolon or comma
    return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]


def ensure_label(session, owner, repo, name, cache):
    if not name:
        return
    if name in cache:
        return
    r = session.get(f"{API}/repos/{owner}/{repo}/labels/{name}")
    if r.status_code == 200:
        cache.add(name)
        return
    # create if missing
    r = session.post(f"{API}/repos/{owner}/{repo}/labels", json={"name": name})
    if r.status_code < 300:
        cache.add(name)
        return
    print(f"[warn] Could not ensure label '{name}': {r.status_code} {r.text}")


def get_milestone_number(session, owner, repo, title, cache):
    if not title:
        return None
    if title in cache:
        return cache[title]

    page = 1
    while True:
        r = session.get(
            f"{API}/repos/{owner}/{repo}/milestones",
            params={"state": "open", "page": page, "per_page": 100},
        )
        if r.status_code >= 300:
            print(f"[warn] List milestones failed: {r.status_code} {r.text}")
            break
        items = r.json()
        if not items:
            break
        for m in items:
            if m.get("title") == title:
                cache[title] = m["number"]
                return m["number"]
        page += 1

    # create if not found
    r = session.post(f"{API}/repos/{owner}/{repo}/milestones", json={"title": title})
    if r.status_code < 300:
        num = r.json()["number"]
        cache[title] = num
        return num
    print(f"[warn] Create milestone '{title}' failed: {r.status_code} {r.text}")
    return None


def post_with_backoff(session, url, payload):
    # tiny backoff to be polite on 403 rate-limit; not exhaustive
    for i in range(3):
        r = session.post(url, json=payload)
        if r.status_code != 403:
            return r
        reset = r.headers.get("x-ratelimit-reset")
        sleep_s = 1.0 * (i + 1)
        if reset and reset.isdigit():
            # sleep up to a small cap if reset is soon
            delta = max(0, int(reset) - int(time.time()))
            sleep_s = min(max(sleep_s, delta), 10)
        time.sleep(sleep_s)
    return r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.token:
        print("Error: supply --token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {args.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    label_cache = set()
    milestone_cache = {}

    with open_csv_robust(args.csv) as f:
        reader = csv.DictReader(f)
        # Validate headers early
        required = {"Title", "Body", "Labels", "Milestone"}
        missing = [h for h in required if h not in (reader.fieldnames or [])]
        if missing:
            print(f"Error: CSV missing headers: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)

        for idx, row in enumerate(
                reader, start=2
        ):  # start=2 accounts for header line as 1
            title = safe_str(row.get("Title"))
            if not title:
                # skip blank lines/rows
                continue

            body = safe_str(row.get("Body"))
            labels = parse_labels(row.get("Labels"))
            milestone_title = safe_str(row.get("Milestone"))
            milestone_num = (
                get_milestone_number(
                    session, args.owner, args.repo, milestone_title, milestone_cache
                )
                if milestone_title
                else None
            )

            for lbl in labels:
                ensure_label(session, args.owner, args.repo, lbl, label_cache)

            payload = {"title": title}
            if body:
                payload["body"] = body
            if labels:
                payload["labels"] = labels
            if milestone_num:
                payload["milestone"] = milestone_num

            if args.dry_run:
                print(f"[DRY RUN] Row {idx}: {payload}")
                continue

            r = post_with_backoff(
                session, f"{API}/repos/{args.owner}/{args.repo}/issues", payload
            )
            if r.status_code >= 300:
                print(f"[error] Row {idx} failed: {r.status_code} {r.text}")
            else:
                print(f"Created: {r.json().get('html_url')}")

            time.sleep(0.25)  # gentle pacing


if __name__ == "__main__":
    main()
