<!-- .github/copilot-instructions.md - guidance for AI coding agents working on the sevensuns repo -->

# sevensuns — Copilot instructions (concise)

This project converts Fantasy Map Generator (FMG) JSON `pack` data into an Obsidian-style vault under the `World/` directory. Use the notes below to be immediately productive.

- Purpose: Convert `map.json` (FMG pack) into Markdown files and save emblems under `World/emblems/`.
- Primary scripts: `fmg_to_obsidian_Version3.py` (current), `fmg_to_obsidian.py` (older copy), and `lore_tools_Version3.py` (lore helpers).

Key architecture & data flow
- Input: a single FMG exported JSON (passed as `map.json` to the script). The code expects `data["pack"]` shape (keys: `cells`, `burgs`, `states`, `provinces`, `cultures`, `religions`, `features`, `rivers`).
- Processing: per-type processors: `process_cells`, `process_burgs`, `process_states`, `process_provinces`, `process_cultures`, `process_religions`, `process_features`, `process_rivers` in `fmg_to_obsidian_Version3.py`.
- Output: `World/` directory with subfolders: `Cells`, `Burgs`, `States`, `Provinces`, `Cultures`, `Religions`, `Features`, `Rivers`, and `emblems`.

Important code conventions and patterns (repo-specific)
- The scripts create the `World/` folder and subfolders at runtime (see `VAULT_DIR` and `folders` list). Don't assume pre-existing directories.
- Many FMG lists in the `pack` are 1-indexed; processors often skip index `0` (e.g., `for b in burgs[1:]:`). Preserve that when modifying loops.
- Frontmatter: `write_markdown` writes a simple YAML-like header but uses `repr()` for values (this is intentional for storing lists/dicts as Python repr). Be cautious when modifying frontmatter serialization — other tools may rely on `repr` rather than strict YAML.
- Emblems: `save_emblem_svg` writes inline SVG from embedded `coa.svg`; `save_emblem_image` copies a file path found in `emblem_url`. Emblem filename pattern: `{type}-{id}.{ext}` and returned paths are `emblems/{filename}`.

Developer workflows & useful commands
- Running conversion (PowerShell):
  - `python fmg_to_obsidian_Version3.py map.json`
  - On Windows standard PowerShell, you can run the batch helper: `.
un_fmg_Version3.bat map.json`
- Quick check: open the `World/` folder to confirm created files (e.g., `World/Cells/Cell-0.md`, `World/Burgs/Burg-1-Name.md`).

Project-specific gotchas & checks
- Validate input shape: processors index deep keys like `pack["cells"]["h"]`, `pack["cells"]["f"]`, `pack["burgs"]` etc. If keys are missing, the script will raise KeyError — add defensive checks if adding pre-processing.
- File naming: spaces in names are replaced with `_` in filenames (see `replace(' ', '_')`).
- Emblem handling: if `emblem_url` is an external URL (HTTP), the current code expects a local path and uses `shutil.copy`; network downloads are not implemented — add a downloader if needed.

Files to inspect for examples
- `fmg_to_obsidian_Version3.py` — canonical implementation to follow when changing output format.
- `fmg_to_obsidian.py` — older copy; use only for reference.
- `lore_tools_Version3.py` — small helpers for generating random lore (non-critical, deterministic tests not provided).

When editing or adding features
- Keep processors small and localized to their functions; tests and orchestration are manual (no test harness present).
- Preserve the frontmatter format unless you update all downstream uses that parse `repr()` values.

If you need to extend the project
- Add a small README snippet under `World/` describing generated file naming for maintainers.
- If adding HTTP emblem fetching, add a flag (e.g., `--download-emblems`) and keep backwards compatibility for local `emblem_url` paths.
- If you want to attach Medieval Fantasy City Generator outputs to Burg pages, add a `--mfcg-dir` flag and implement per-burg copy/link behavior. See `World/README.md` for expected behavior and examples.

Questions or unclear areas
- The top-level `README.md` is minimal; tell me how much more detail you'd like (usage examples, sample `map.json`, CI commands) and I will update this file.

---
Please review and tell me if you want more detail on running, adding tests, or changing frontmatter formatting.
