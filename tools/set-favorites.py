#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Update the favorites list in catalog.json from an exported favorites.json.

Usage:
    python3 tools/set-favorites.py favorites.json
    python3 tools/set-favorites.py favorites.json --dry-run
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(ROOT, "catalog.json")


def main():
    ap = argparse.ArgumentParser(description="Set catalog.json favorites from an exported file.")
    ap.add_argument("file", help="path to a favorites.json exported from the meal planner")
    ap.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as fh:
        new_favs = json.load(fh)
    if not isinstance(new_favs, list) or not all(isinstance(x, str) for x in new_favs):
        sys.exit("Error: expected a JSON array of recipe id strings.")

    with open(CATALOG_PATH, encoding="utf-8") as fh:
        catalog = json.load(fh)

    recipe_ids = set()
    for path in catalog.get("recipes", []):
        recipe_ids.add(os.path.splitext(os.path.basename(path))[0])

    unknown = [f for f in new_favs if f not in recipe_ids]
    if unknown:
        print(f"Warning: skipping {len(unknown)} id(s) not in catalog: {', '.join(unknown)}")
        new_favs = [f for f in new_favs if f in recipe_ids]

    old_favs = catalog.get("favorites", [])
    added = sorted(set(new_favs) - set(old_favs))
    removed = sorted(set(old_favs) - set(new_favs))

    if not added and not removed:
        print("Favorites already match — nothing to change.")
        return

    if added:
        print(f"Adding {len(added)}: {', '.join(added)}")
    if removed:
        print(f"Removing {len(removed)}: {', '.join(removed)}")

    if args.dry_run:
        print("\n(dry-run: catalog.json not written)")
        return

    catalog["favorites"] = sorted(new_favs)
    with open(CATALOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\nWrote catalog.json with {len(new_favs)} favorite(s).")


if __name__ == "__main__":
    main()
