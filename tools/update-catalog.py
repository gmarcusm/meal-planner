#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Rebuild catalog.json from the recipes/ directory.

Scans recipes/*.html and updates catalog.json:
  - Adds new recipes (appended at the end, in alphabetical order among new ones).
  - Keeps the existing order for recipes already in the catalog.
  - Removes entries whose HTML files no longer exist (unless --keep-missing).
  - Preserves the favorites list and comment keys.

Usage:
    python3 tools/update-catalog.py
    python3 tools/update-catalog.py --keep-missing   # don't remove missing files
    python3 tools/update-catalog.py --dry-run        # print diff without writing
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(ROOT, "catalog.json")
RECIPES_DIR = os.path.join(ROOT, "recipes")


def main():
    ap = argparse.ArgumentParser(description="Rebuild catalog.json from recipes/ directory.")
    ap.add_argument("--keep-missing", action="store_true",
                    help="keep catalog entries whose HTML files are missing (don't remove them)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would change without writing catalog.json")
    args = ap.parse_args()

    # Paths on disk — relative to repo root, forward slashes
    on_disk = sorted(
        "recipes/" + os.path.basename(p)
        for p in glob.glob(os.path.join(RECIPES_DIR, "*.html"))
    )
    disk_set = set(on_disk)

    # Load existing catalog
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, encoding="utf-8") as fh:
            catalog = json.load(fh)
    else:
        catalog = {"recipes": [], "favorites": []}

    existing = catalog.get("recipes", [])
    existing_set = set(existing)

    added = sorted(disk_set - existing_set)
    removed = [p for p in existing if p not in disk_set]

    # Build new list: keep existing order, drop missing, append new
    new_list = [p for p in existing if p in disk_set or args.keep_missing]
    new_list += added

    # Report
    if added:
        print(f"Adding {len(added)} recipe(s):")
        for p in added:
            print(f"  + {p}")
    if removed and not args.keep_missing:
        print(f"Removing {len(removed)} recipe(s) (file not found):")
        for p in removed:
            print(f"  - {p}")
    if not added and not (removed and not args.keep_missing):
        print("catalog.json is already up to date.")
        return

    if args.dry_run:
        print("\n(dry-run: catalog.json not written)")
        return

    catalog["recipes"] = new_list
    with open(CATALOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\nWrote catalog.json ({len(new_list)} recipes).")


if __name__ == "__main__":
    main()
