#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate data-only JSON sidecars for the meal planner.

For each ``recipes/*.html`` file, extract the embedded ``#recipe-data`` JSON
block and write ``recipes/<name>.json`` next to it. The planner (index.html)
loads the sidecar in preference to fetching and DOM-parsing the full HTML,
which is much faster for a large catalog.

By default each sidecar keeps only the ``main`` image (used for the catalog
thumbnail) and drops the per-step images. Pass ``--no-images`` for tiny,
text-only sidecars — the catalog then shows no thumbnails when it loads from
the sidecars.

Usage:
    python3 tools/make-sidecars.py            # keep main image (thumbnails)
    python3 tools/make-sidecars.py --no-images
"""
import argparse
import base64
import glob
import io
import json
import os
import re
import sys

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPES_DIR = os.path.join(ROOT, "recipes")
DATA_RE = re.compile(r'<script id="recipe-data"[^>]*>(.*?)</script>', re.S)


def downscale_data_uri(uri, max_width, quality):
    """Shrink a base64 image data URI to a small JPEG thumbnail data URI."""
    _, b64 = uri.split(",", 1)
    im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    im.thumbnail((max_width, 100000), Image.LANCZOS)   # preserve aspect, never upscale
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def main():
    ap = argparse.ArgumentParser(description="Generate JSON sidecars for recipe HTML files.")
    ap.add_argument("--no-images", action="store_true",
                    help="omit all images (smallest sidecars; no catalog thumbnails)")
    ap.add_argument("--thumb-width", type=int, default=480,
                    help="max thumbnail width in px when downscaling (default 480; needs Pillow)")
    ap.add_argument("--quality", type=int, default=72,
                    help="JPEG quality for downscaled thumbnails (default 72; needs Pillow)")
    args = ap.parse_args()

    html_files = sorted(glob.glob(os.path.join(RECIPES_DIR, "*.html")))
    if not html_files:
        sys.exit(f"No recipe HTML files found in {RECIPES_DIR}")

    html_total = json_total = 0
    written = skipped = 0
    for path in html_files:
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        m = DATA_RE.search(html)
        if not m:
            print(f"  skip (no #recipe-data): {os.path.basename(path)}")
            skipped += 1
            continue
        data = json.loads(m.group(1))

        # Trim images: keep only `main` for the thumbnail (downscaled if Pillow
        # is available), or drop entirely.
        imgs = data.get("images") or {}
        if args.no_images:
            data.pop("images", None)
        else:
            main = imgs.get("main")
            if main and HAVE_PIL and main.startswith("data:"):
                try:
                    main = downscale_data_uri(main, args.thumb_width, args.quality)
                except Exception as exc:  # keep the original on any decode/encode error
                    print(f"  warn (thumbnail not resized): {os.path.basename(path)}: {exc}")
            data["images"] = {"main": main} if main else {}

        out_path = os.path.splitext(path)[0] + ".json"
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)

        html_total += os.path.getsize(path)
        json_total += len(text.encode("utf-8"))
        written += 1

    print(f"\nWrote {written} sidecar(s)" + (f", skipped {skipped}" if skipped else "") + ".")
    if html_total:
        print(f"HTML total: {html_total / 1024 / 1024:6.2f} MB")
        print(f"JSON total: {json_total / 1024 / 1024:6.2f} MB  "
              f"({100 * json_total / html_total:.0f}% of the HTML)")
    if not args.no_images:
        if HAVE_PIL:
            print(f"Thumbnails downscaled to <= {args.thumb_width}px (JPEG q{args.quality}).")
        else:
            print("Pillow not installed — main images kept full size. "
                  "Install Pillow (e.g. in a venv) for small thumbnails.")


if __name__ == "__main__":
    main()
