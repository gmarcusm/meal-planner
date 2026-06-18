#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Usage: python3 set_image.py <image_file> <recipe.html>

Resizes the image to max 900px wide and embeds it as the main photo
in the recipe HTML file.

Example:
    python3 set_image.py ~/Downloads/shakshuka.jpg recipes/shakshuka.html
"""
import sys, re, json, base64, io
from pathlib import Path
from PIL import Image

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    img_path  = Path(sys.argv[1]).expanduser()
    html_path = Path(sys.argv[2]).expanduser()

    if not img_path.exists():
        sys.exit(f"Image not found: {img_path}")
    if not html_path.exists():
        sys.exit(f"HTML file not found: {html_path}")

    # Encode image
    pil = Image.open(img_path)
    if pil.width > 900:
        pil = pil.resize((900, int(pil.height * 900 / pil.width)), Image.LANCZOS)
    buf = io.BytesIO()
    pil.convert("RGB").save(buf, "JPEG", quality=85)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    # Patch HTML
    html = html_path.read_text(encoding="utf-8")
    m = re.search(r'(<script id="recipe-data" type="application/json">)(.*?)(</script>)',
                  html, re.DOTALL)
    if not m:
        sys.exit("No recipe-data JSON block found in the HTML file.")

    data = json.loads(m.group(2))
    data["images"]["main"] = b64
    new_html = html[:m.start(2)] + json.dumps(data, ensure_ascii=False, indent=2) + html[m.end(2):]
    html_path.write_text(new_html, encoding="utf-8")

    print(f"✓ {html_path.name} updated ({len(b64) // 1024} KB image)")

if __name__ == "__main__":
    main()
