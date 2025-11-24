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

Local emblems
-------------

- You can provide local emblem image files by placing them in the vault's `emblems/` folder or by setting an absolute local path in the `emblem_url` field of a burg/state/province object in the FMG `pack`.
- The converter will copy local files into the vault `emblems/` directory. If the source file already resides in the `emblems/` folder and has the same filename, the converter will reuse the existing file instead of creating a duplicate.
- To enable automatic HTTP/HTTPS downloads for remote emblem URLs, run the script with `--download-emblems` and ensure `requests` is installed (see `requirements.txt`).

Example usage:

```powershell
python .\fmg_to_obsidian_Version3.py .\map.json --outdir World --download-emblems
```

If you prefer not to download remote images, set `emblem_url` to a local absolute path and run the converter without `--download-emblems`.
