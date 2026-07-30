#!/usr/bin/env python3
"""Refresh `latest/<App>-latest.apk` to point at the newest build in `repo/`.

The download buttons on https://www.enpleineconscience.ch/retreat-tools link to
these stable filenames, so the page keeps working without being edited at every
release. Run this after `fdroid update` (which is what writes the index this
reads), then commit and push.

The copies deliberately live in `latest/`, NOT in `repo/`: anything inside
`repo/` is scanned by `fdroid update`, and a second file with the same
versionCode would be indexed as a duplicate of the release it copies.
"""

import hashlib
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
INDEX = HERE / "repo" / "index-v2.json"
LATEST = HERE / "latest"

# package id -> stable filename served to the website
APPS = {
    "com.freedomfighter.retreattimer": "RetreatTimer-latest.apk",
    "com.freedomfighter.retreatplayer": "RetreatPlayer-latest.apk",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not INDEX.exists():
        sys.exit(f"{INDEX} not found — run `fdroid update` first.")

    index = json.loads(INDEX.read_text())
    LATEST.mkdir(exist_ok=True)
    changed = False

    for package, stable_name in APPS.items():
        entry = index["packages"].get(package)
        if entry is None:
            print(f"!  {package}: not in the index, skipped")
            continue

        newest = max(
            entry["versions"].values(),
            key=lambda v: v["manifest"]["versionCode"],
        )
        source = HERE / "repo" / newest["file"]["name"].lstrip("/")
        target = LATEST / stable_name
        version = newest["manifest"]["versionName"]

        if not source.exists():
            print(f"!  {package}: {source.name} missing from repo/, skipped")
            continue

        if target.exists() and digest(target) == digest(source):
            print(f"=  {stable_name} already is {source.name} (v{version})")
            continue

        shutil.copy2(source, target)
        changed = True
        print(f"→  {stable_name} now is {source.name} (v{version})")

    if changed:
        print("\nCommit and push fdroid-repo to publish the new downloads.")


if __name__ == "__main__":
    main()
