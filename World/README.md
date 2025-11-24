# World vault (generated)

This folder is populated by the `fmg_to_obsidian_Version3.py` converter. It contains an Obsidian-style vault of Markdown files representing the map data from an FMG `map.json`.

Layout
- `Cells/` — one file per cell: `Cell-<id>.md`.
- `Burgs/` — settlements: `Burg-<id>-<name>.md` (spaces replaced with `_`).
- `States/`, `Provinces/`, `Cultures/`, `Religions/`, `Features/`, `Rivers/` — one file per entity with names like `State-<id>-<name>.md`.
- `emblems/` — saved emblem image or SVG files. Filenames follow the pattern `<type>-<id>.<ext>` (e.g., `burg-1.png`, `state-2.svg`).

Notes for maintainers
- Filename patterns: names use `replace(' ', '_')` when generating file names.
- Emblems: the converter either writes embedded SVG (`coa.svg`) or copies a local `emblem_url` path into `emblems/`.
- Frontmatter: values are serialized with `repr()` (Python representation). Consumers of these files should read Python-style literals (e.g., `True/False`, lists as `[...]`).
- Running the converter (PowerShell):

```powershell
python fmg_to_obsidian_Version3.py map.json
# or
.\run_fmg_Version3.bat map.json
```

- If `emblem_url` points to an HTTP URL, the current script does not download it — it expects a local path. Add a downloader flag (for example `--download-emblems`) if you want automatic HTTP fetching.

MFCG (Medieval Fantasy City Generator) integration
-----------------------------------------------

If you have outputs from the Medieval Fantasy City Generator (MFCG) you can attach them to matching Burg pages during conversion. Provide the path to the folder containing MFCG exports using the `--mfcg-dir` CLI flag.

Behavior:
- The converter searches the provided directory for folders or files that match a burg by ID or name (examples: `Burg-1`, `1`, `Stonehaven`, `Burg-1-Stonehaven`).
- If matches are found the script copies those files/folders into `World/Burgs/Burg-<id>-<name>/mfcg/` and adds a `mfcg_assets` frontmatter list with vault-relative paths and links in the generated Markdown.

Example usage:

```powershell
python .\fmg_to_obsidian_Version3.py .\map.json --outdir World --mfcg-dir C:\path\to\mfcg-exports
```

Local emblems
-------------

- You can provide local emblem image files by placing them in the vault's `emblems/` folder or by setting an absolute local path in the `emblem_url` field of a burg/state/province object in the FMG `pack`.
- The converter will copy local files into the vault `emblems/` directory. If the source file already resides in the `emblems/` folder and has the same filename, the converter will reuse the existing file instead of creating a duplicate.
- To enable automatic HTTP/HTTPS downloads for remote emblem URLs, run the script with `--download-emblems` and ensure `requests` is installed (see `requirements.txt`).

Example usage:

```powershell
python .\fmg_to_obsidian_Version3.py .\map.json --outdir World --download-emblems
```

MFCG matching, dedupe and ZIP options
-----------------------------------

The converter offers extra control when attaching Medieval Fantasy City Generator (MFCG) assets:

- `--mfcg-match` (default: fuzzy) — matching strategy for finding MFCG assets in the provided `--mfcg-dir`:
	- `fuzzy` — case-insensitive substring checks (matches many common names)
	- `exact` — strict filename equality against `burg-<id>`, `<id>`, or the sanitized burg name
	- `regex` — provide a Python regular expression with `--mfcg-match-pattern` to match filenames
	- `map` — use a JSON map file (`--mfcg-map-file`) containing explicit mappings from burg ids/names to relative asset paths

- `--mfcg-dedupe` — enable deduplication by file content (sha256). If a matching file already exists in the vault with identical content, the converter will reuse the existing vault-relative path instead of copying a duplicate.

- `--mfcg-zip` — after copying matched assets, create a per-burg ZIP archive and remove the individual copied files (saves space for large exports). The converter returns a single archive path as the `mfcg_assets` entry when this mode is used.

Example:

```powershell
python .\fmg_to_obsidian_Version3.py map.json --outdir World --mfcg-dir C:\mfcg-exports --mfcg-match exact --mfcg-dedupe --mfcg-zip
```

If you prefer not to download remote images, set `emblem_url` to a local absolute path and run the converter without `--download-emblems`.
