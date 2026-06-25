# Recipes

Recipes , Menus and Co.

Things here might be in Spanish, English, or German.

## Meal Planner

`index.html` is a standalone web app: pick recipes for the week, set servings, and
export a combined shopping list (text, PDF, or Apple Reminders). It reads its catalog
from `catalog.json`, which lists the recipe HTML files in the `recipes/` folder (the
`schweinefilet-honig-rosmarin.html` format, with an embedded `#recipe-data` JSON block).

### Running it

The app must be served over HTTP — opening `index.html` directly with `file://` will
not work, because the browser blocks it from loading `catalog.json` and the recipe files.

From this directory, start any static web server, e.g.:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/> in your browser. Press `Ctrl+C` to stop the server.

(Any static server works — e.g. `npx serve` or `php -S localhost:8000` — if you'd rather
not use Python.)

### Adding recipes

Add a recipe by converting it to the `schweinefilet-honig-rosmarin.html` format and
placing it in the `recipes/` folder. Then update the catalog:

```bash
python3 tools/update-catalog.py
```

This scans `recipes/*.html` and syncs `catalog.json` — adding new files, removing
entries whose HTML is gone, and preserving the existing order and favorites list.
Pass `--dry-run` to preview changes without writing, or `--keep-missing` to skip
removal of files that are no longer on disk.

If a data-only sibling JSON exists next to a recipe (e.g. `recipes/foo.json` beside
`recipes/foo.html`), the planner loads that instead for speed.

### Adding or replacing a recipe photo

To embed a photo into a recipe HTML file:

```bash
python3 tools/set_image.py ~/Downloads/photo.jpg recipes/foo.html
```

The image is resized to at most 900 px wide and embedded as a base64 JPEG directly
in the HTML file. After updating a photo, re-run `make-sidecars.py` to refresh the
catalog thumbnails.

### Speeding up loading (JSON sidecars)

The planner loads each recipe's data from the HTML file by default, which means
downloading and parsing the full page (embedded images included). For a large
catalog that gets slow. Generate lightweight JSON sidecars instead:

```bash
python3 tools/make-sidecars.py
```

This writes a `recipes/<name>.json` next to each `recipes/<name>.html`. The
planner loads the sidecar in preference to the HTML, skipping the slow parse.
By default sidecars keep the main image (for the catalog thumbnail) and drop the
per-step images; pass `--no-images` for tiny, text-only sidecars (no thumbnails).

**Smaller thumbnails (recommended):** install [Pillow](https://python-pillow.org/)
and the script downscales each main image to a ~480px JPEG, shrinking the whole
catalog from ~14 MB of HTML to ~2 MB of sidecars while keeping thumbnails:

```bash
python3 -m venv .venv
.venv/bin/pip install Pillow
.venv/bin/python tools/make-sidecars.py        # --thumb-width / --quality to tune
```

Without Pillow the main images are kept at full size (still works, just larger).

Re-run the script whenever you add or change a recipe — sidecars are generated
artifacts derived from the HTML.

### Favorites

Click the ★ on a recipe to mark it a favorite; favorites are grouped at the top of the
catalog. Toggling is stored per-browser (a static page can't write back to the server),
so it follows the device. To ship default favorites, list recipe ids in the optional
`favorites` array in `catalog.json` — those apply only on a browser's first visit, before
so it follows the device.

To ship default favorites so new visitors see them pre-selected, click the
**↓ Export** button in the Favorites heading to download a `favorites.json`, then run:

```bash
python3 tools/set-favorites.py favorites.json
```

This updates the `favorites` array in `catalog.json`. Pass `--dry-run` to preview
changes without writing. The defaults apply only on a browser's first visit, before
any star is clicked.
