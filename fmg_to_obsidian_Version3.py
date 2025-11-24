import argparse
import json
try:
    import yaml
    _HAS_YAML = True
except Exception:
    yaml = None
    _HAS_YAML = False
import logging
import os
import re
import shutil
import requests
from pathlib import Path

# HTTP session reused for downloads; set a permissive User-Agent to reduce 403s
_HTTP_SESSION = None
try:
    _HTTP_SESSION = requests.Session()
    _HTTP_SESSION.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; sevensuns/1.0; +https://github.com)"
    })
except Exception:
    _HTTP_SESSION = None

# Default output vault directory (can be overridden by CLI)
VAULT_DIR = "World"
EMBLEM_DIR = os.path.join(VAULT_DIR, "emblems")
DOWNLOAD_EMBLEMS = False
MFCG_DIR = None

def ensure_vault_dirs(outdir):
    folders = [
        "Cells", "Burgs", "States", "Provinces",
        "Cultures", "Religions", "Features", "Rivers", "emblems"
    ]
    for folder in folders:
        os.makedirs(os.path.join(outdir, folder), exist_ok=True)

def write_markdown(path, frontmatter, body):
    """Write a Markdown file with YAML frontmatter + body.

    If PyYAML is available it will be used to produce valid YAML. Otherwise
    falls back to the previous `repr()` formatting for compatibility.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        if _HAS_YAML:
            try:
                # Use safe_dump to avoid non-YAML types; keep block style
                yaml_text = yaml.safe_dump(frontmatter, sort_keys=False, default_flow_style=False)
                # PyYAML may append '...'; strip if present and ensure newline
                if yaml_text.endswith("...\n"):
                    yaml_text = yaml_text[:-4]
                f.write(yaml_text)
            except Exception:
                # Fall back to repr if yaml.dump fails for unexpected types
                for k, v in frontmatter.items():
                    f.write(f"{k}: {repr(v)}\n")
        else:
            for k, v in frontmatter.items():
                f.write(f"{k}: {repr(v)}\n")
        f.write("---\n\n")
        f.write(body)


def safe_filename(name: str, fallback: str = "unnamed") -> str:
    """Return a filesystem-safe filename fragment for `name`.

    Replaces disallowed characters with underscores and trims the result.
    """
    if not name:
        return fallback
    s = str(name)
    # Replace whitespace with underscore, then remove characters outside allowed set
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9._-]", "_", s)
    s = s.strip("_-")
    return s or fallback


def _get_list_item(lst, idx, default=None):
    """Safely get `lst[idx]` returning `default` if out-of-range or not a list."""
    try:
        if isinstance(lst, dict):
            # dict keyed by indices
            return lst.get(idx, default)
        if lst is None:
            return default
        return lst[idx] if 0 <= idx < len(lst) else default
    except Exception:
        return default


def _safe_cast(val, caster, default=None):
    try:
        return caster(val)
    except Exception:
        return default


def save_emblem_svg(obj_type, obj_id, svg_data):
    filename = f"{obj_type}-{obj_id}.svg"
    path = os.path.join(EMBLEM_DIR, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_data)
        return f"emblems/{filename}"
    except OSError as e:
        logging.warning("Failed to write SVG emblem %s: %s", path, e)
        return ""


def get_emblem_for(obj_type, obj, obj_id):
    """Resolve and save an emblem for an object.

    Checks for an embedded `coa.svg` field, then `emblem_url` (local path or URL).
    Returns the vault-relative path (e.g., 'emblems/burg-1.svg') or an empty string.
    """
    try:
        # embedded SVG from COA
        coa = obj.get("coa") if isinstance(obj, dict) else None
        if isinstance(coa, dict) and "svg" in coa:
            return save_emblem_svg(obj_type, obj_id, coa["svg"])

        # external emblem URL or local path
        emblem_src = obj.get("emblem_url") if isinstance(obj, dict) else None
        if emblem_src:
            ext = str(emblem_src).split(".")[-1]
            return save_emblem_image(emblem_src, obj_type, obj_id, ext, download=DOWNLOAD_EMBLEMS)
    except Exception as e:
        logging.warning("Failed to resolve emblem for %s %s: %s", obj_type, obj_id, e)
    return ""

def save_emblem_image(src_path, obj_type, obj_id, ext="png", download=False):
    filename = f"{obj_type}-{obj_id}.{ext}"
    dst_path = os.path.join(EMBLEM_DIR, filename)
    # If src_path is a URL and download allowed, attempt to download
    if isinstance(src_path, str) and src_path.startswith(("http://", "https://")):
        if not download:
            logging.warning("Emblem URL provided but --download-emblems not set: %s", src_path)
            return ""
        try:
            sess = _HTTP_SESSION or requests
            resp = sess.get(src_path, stream=True, timeout=10)
            resp.raise_for_status()
            # Ensure emblem dir exists
            os.makedirs(EMBLEM_DIR, exist_ok=True)
            with open(dst_path, "wb") as out_file:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        out_file.write(chunk)
            return f"emblems/{filename}"
        except requests.RequestException as e:
            logging.warning("Failed to download emblem %s: %s", src_path, e)
            return ""

    # Otherwise expect a local path
    try:
        # If source path is already the destination, avoid copying / duplication
        abs_dst = os.path.abspath(dst_path)
        try:
            abs_src = os.path.abspath(src_path)
        except Exception:
            abs_src = None

        # If source and destination are the same file, reuse it
        if abs_src and abs_src == abs_dst:
            logging.debug("Source emblem is already at destination: %s", abs_src)
            return f"emblems/{filename}"

        # If the source already lives in the emblem folder and has the same basename,
        # reuse it (no copy) to avoid duplicate files.
        try:
            emblem_dir_abs = os.path.abspath(EMBLEM_DIR)
            if abs_src and os.path.dirname(abs_src) == emblem_dir_abs and os.path.basename(abs_src) == filename:
                logging.debug("Source emblem already in emblem dir: %s", abs_src)
                return f"emblems/{filename}"
        except Exception:
            pass

        if not os.path.exists(src_path):
            logging.warning("Local emblem file not found: %s", src_path)
            return ""
        shutil.copy(src_path, dst_path)
        return f"emblems/{filename}"
    except (OSError, TypeError) as e:
        logging.warning("Failed to copy emblem %s -> %s: %s", src_path, dst_path, e)
        return ""


def integrate_mfcg_assets(burg_id, burg_name, mfcg_root, outdir):
    """Find and copy MFCG outputs that match a burg into the vault.

    Strategy:
    - Look for directories in `mfcg_root` matching `burg-<id>`, `<id>`, or the safe filename of the burg name.
    - If found, copy their contents into `outdir/Burgs/Burg-<id>-<safe_name>/mfcg/<folder>`
    - If no matching folders, search for files in `mfcg_root` that contain the id or safe name and copy them into the per-burg mfcg folder.

    Returns a list of vault-relative paths to the copied files (empty list if none).
    """
    try:
        if not mfcg_root:
            return []
        src_root = os.path.abspath(mfcg_root)
        if not os.path.exists(src_root):
            logging.debug("MFCG root not found: %s", src_root)
            return []

        safe_name = safe_filename(burg_name)
        candidates = []
        # look for matching directories
        for entry in os.listdir(src_root):
            entry_low = entry.lower()
            if entry_low in (f"burg-{burg_id}", str(burg_id), safe_name.lower()) or \
               f"burg-{burg_id}" in entry_low or safe_name.lower() in entry_low:
                cand = os.path.join(src_root, entry)
                candidates.append(cand)

        dest_base = os.path.join(outdir, "Burgs", f"Burg-{burg_id}-{safe_name}", "mfcg")
        os.makedirs(dest_base, exist_ok=True)
        copied = []

        # If candidate directories exist, copy them (preserve inner structure)
        for c in candidates:
            if os.path.isdir(c):
                # copy folder contents into subfolder named after the source
                dest_sub = os.path.join(dest_base, os.path.basename(c))
                # If dest_sub exists, use it; otherwise copytree
                if os.path.exists(dest_sub):
                    logging.debug("MFCG dest already exists, skipping copy: %s", dest_sub)
                else:
                    try:
                        shutil.copytree(c, dest_sub)
                    except Exception:
                        # fallback: copy files inside
                        os.makedirs(dest_sub, exist_ok=True)
                        for root, dirs, files in os.walk(c):
                            rel = os.path.relpath(root, c)
                            target_root = os.path.join(dest_sub, rel) if rel != '.' else dest_sub
                            os.makedirs(target_root, exist_ok=True)
                            for f in files:
                                shutil.copy(os.path.join(root, f), os.path.join(target_root, f))
                # Collect vault-relative paths
                for root, _, files in os.walk(dest_sub):
                    for f in files:
                        rel = os.path.relpath(os.path.join(root, f), outdir).replace('\\', '/')
                        copied.append(rel)

        # Also try file matches at root (do this even if directories copied so we
        # include both kinds of assets when present)
        #
        # This copies any file at the root of mfcg_root whose name contains a
        # matching token (burg-id or safe name).
            for entry in os.listdir(src_root):
                entry_low = entry.lower()
                if (f"burg-{burg_id}" in entry_low) or (str(burg_id) in entry_low) or (safe_name.lower() in entry_low):
                    abs_src = os.path.join(src_root, entry)
                    if os.path.isfile(abs_src):
                        dst = os.path.join(dest_base, entry)
                        try:
                            shutil.copy(abs_src, dst)
                            rel = os.path.relpath(dst, outdir).replace('\\', '/')
                            copied.append(rel)
                        except Exception as e:
                            logging.warning("Failed to copy MFCG file %s -> %s: %s", abs_src, dst, e)

        return copied
    except Exception as e:
        logging.warning("Unexpected error integrating MFCG assets for %s: %s", burg_id, e)
        return []

def process_cells(pack):
    cells = pack.get("cells", {})
    # Some packs may provide `cells` as a list of heights instead of a dict
    if isinstance(cells, list):
        cells = {"h": cells}
    heights = cells.get("h", [])
    for cid, elev in enumerate(heights):
        try:
            fm = {
                "cell_id": cid,
                "x": _safe_cast(_get_list_item(cells.get("x", []), cid, 0), float, 0.0),
                "y": _safe_cast(_get_list_item(cells.get("y", []), cid, 0), float, 0.0),
                "elevation": _safe_cast(elev, int, 0),
                "feature": _safe_cast(_get_list_item(cells.get("f", []), cid, 0), int, 0),
                "biome": _safe_cast(_get_list_item(cells.get("biome", []), cid, 0), int, 0),
                "burg": _safe_cast(_get_list_item(cells.get("burg", []), cid, 0), int, 0),
                "culture": _safe_cast(_get_list_item(cells.get("culture", []), cid, 0), int, 0),
                "state": _safe_cast(_get_list_item(cells.get("state", []), cid, 0), int, 0),
                "province": _safe_cast(_get_list_item(cells.get("province", []), cid, 0), int, 0),
                "religion": _safe_cast(_get_list_item(cells.get("religion", []), cid, 0), int, 0),
                "population": _safe_cast(_get_list_item(cells.get("pop", []), cid, 0.0), float, 0.0),
                "river": _safe_cast(_get_list_item(cells.get("r", []), cid, 0), int, 0),
                "flux": _safe_cast(_get_list_item(cells.get("fl", []), cid, 0), int, 0),
                "harbor_score": _safe_cast(_get_list_item(cells.get("harbor", []), cid, 0), int, 0),
                "routes": {},
            }
            routes = cells.get("routes", {})
            if isinstance(routes, dict):
                fm["routes"] = routes.get(cid, {})
            elif isinstance(routes, list):
                fm["routes"] = _get_list_item(routes, cid, {})
            else:
                fm["routes"] = {}
        except Exception as e:
            logging.warning("Skipping cell %s due to error: %s", cid, e)
            continue
        body = (
            f"# Cell {fm['cell_id']}\n"
            f"Links → [[Features/Feature-{fm['feature']}]], "
            f"[[Cultures/Culture-{fm['culture']}]], [[States/State-{fm['state']}]], "
            f"[[Provinces/Province-{fm['province']}]], [[Religions/Religion-{fm['religion']}]], "
            f"[[Rivers/River-{fm['river']}]], [[Burgs/Burg-{fm['burg']}]]"
        )
        path = os.path.join(VAULT_DIR, "Cells", f"Cell-{cid}.md")
        write_markdown(path, fm, body)

def process_burgs(burgs):
    if not isinstance(burgs, list):
        logging.warning("burgs is not a list; skipping burg processing")
        return
    for b in burgs[1:]:  # skip element 0
        try:
            if not isinstance(b, dict):
                logging.warning("Skipping non-dict burg entry: %s", repr(b))
                continue
            emblem_url = get_emblem_for("burg", b, b.get("i", "unknown"))
            fm = {
                "burg_id": b.get("i", 0),
                "name": b.get("name", ""),
                "cell": b.get("cell", 0),
                "culture": b.get("culture", 0),
                "state": b.get("state", 0),
                "feature": b.get("feature", 0),
                "population": b.get("population", 0),
                "type": b.get("type", ""),
                "capital": b.get("capital", False),
                "port": b.get("port", False),
                "citadel": b.get("citadel", False),
                "plaza": b.get("plaza", False),
                "temple": b.get("temple", False),
                "walls": b.get("walls", False),
                "emblem_url": emblem_url,
            }
        except Exception as e:
            logging.warning("Skipping burg entry due to error: %s", e)
            continue
        # Integrate Medieval Fantasy City Generator (MFCG) assets, if a source dir was provided
        mfcg_assets = []
        try:
            if isinstance(MFCG_DIR, str) and MFCG_DIR:
                mfcg_assets = integrate_mfcg_assets(fm['burg_id'], fm['name'], MFCG_DIR, VAULT_DIR)
        except Exception:
            logging.debug("MFCG asset integration failed for burg %s", fm.get('burg_id'))

        body = (
            f"# Burg {fm['name']}\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"Located in [[Cells/Cell-{fm['cell']}]]\n"
            f"Culture → [[Cultures/Culture-{fm['culture']}]]\n"
            f"State → [[States/State-{fm['state']}]]\n"
            f"Feature → [[Features/Feature-{fm['feature']}]]"
        )
        # Append links to any integrated MFCG assets
        if mfcg_assets:
            body += "\n\nMFCG assets:\n"
            for a in mfcg_assets:
                # a is a vault-relative path
                body += f"- [{os.path.basename(a)}]({a})\n"
            fm['mfcg_assets'] = mfcg_assets
        else:
            fm['mfcg_assets'] = []
        filename = f"Burg-{fm['burg_id']}-{safe_filename(fm['name'])}.md"
        path = os.path.join(VAULT_DIR, "Burgs", filename)
        write_markdown(path, fm, body)

def process_states(states):
    if not isinstance(states, list):
        logging.warning("states is not a list; skipping state processing")
        return
    for s in states[1:]:
        try:
            if not isinstance(s, dict):
                logging.warning("Skipping non-dict state entry: %s", repr(s))
                continue
            emblem_url = get_emblem_for("state", s, s.get("i", "unknown"))
            fm = {
                "state_id": s.get("i", 0),
                "name": s.get("name", ""),
                "form": s.get("form", ""),
                "culture": s.get("culture", 0),
                "capital_burg": s.get("capital", 0),
                "provinces": s.get("provinces", []),
                "neighbors": s.get("neighbors", []),
                "burgs": s.get("burgs", []),
                "emblem_url": emblem_url,
            }
        except Exception as e:
            logging.warning("Skipping state entry due to error: %s", e)
            continue
        body = (
            f"# State {fm['name']}\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"Culture → [[Cultures/Culture-{fm['culture']}]]\n"
            f"Capital → [[Burgs/Burg-{fm['capital_burg']}]]"
        )
        filename = f"State-{fm['state_id']}-{safe_filename(fm['name'])}.md"
        path = os.path.join(VAULT_DIR, "States", filename)
        write_markdown(path, fm, body)

def process_provinces(provinces):
    if not isinstance(provinces, list):
        logging.warning("provinces is not a list; skipping province processing")
        return
    for p in provinces[1:]:
        try:
            if not isinstance(p, dict):
                logging.warning("Skipping non-dict province entry: %s", repr(p))
                continue
            emblem_url = get_emblem_for("province", p, p.get("i", "unknown"))
            fm = {
                "province_id": p.get("i", 0),
                "name": p.get("name", ""),
                "state": p.get("state", 0),
                "capital_burg": p.get("burg", 0),
                "burgs": p.get("burgs", []),
                "cells": p.get("cells", []),
                "emblem_url": emblem_url,
            }
        except Exception as e:
            logging.warning("Skipping province entry due to error: %s", e)
            continue
        body = (
            f"# Province {fm['name']}\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"State → [[States/State-{fm['state']}]]\n"
            f"Capital → [[Burgs/Burg-{fm['capital_burg']}]]"
        )
        filename = f"Province-{fm['province_id']}-{safe_filename(fm['name'])}.md"
        path = os.path.join(VAULT_DIR, "Provinces", filename)
        write_markdown(path, fm, body)

def process_cultures(cultures):
    if not isinstance(cultures, list):
        logging.warning("cultures is not a list; skipping culture processing")
        return
    for c in cultures[1:]:
        try:
            if not isinstance(c, dict):
                logging.warning("Skipping non-dict culture entry: %s", repr(c))
                continue
            emblem_url = get_emblem_for("culture", c, c.get("i", "unknown"))
            fm = {
                "culture_id": c.get("i", 0),
                "name": c.get("name", ""),
                "origins": c.get("origins", []),
                "states": [],
                "burgs": [],
                "color": c.get("color", ""),
                "expansionism": c.get("expansionism", 1.0),
                "emblem_url": emblem_url,
            }
        except Exception as e:
            logging.warning("Skipping culture entry due to error: %s", e)
            continue
        body = (
            f"# Culture {fm['name']}\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"Origins → {fm['origins']}"
        )
        filename = f"Culture-{fm['culture_id']}-{safe_filename(fm['name'])}.md"
        path = os.path.join(VAULT_DIR, "Cultures", filename)
        write_markdown(path, fm, body)

def process_religions(religions):
    if not isinstance(religions, list):
        logging.warning("religions is not a list; skipping religion processing")
        return
    for r in religions[1:]:
        try:
            if not isinstance(r, dict):
                logging.warning("Skipping non-dict religion entry: %s", repr(r))
                continue
            emblem_url = get_emblem_for("religion", r, r.get("i", "unknown"))
            fm = {
                "religion_id": r.get("i", 0),
                "name": r.get("name", ""),
                "type": r.get("type", ""),
                "deity": r.get("deity", ""),
                "culture": r.get("culture", 0),
                "states": [],
                "cells": [],
                "emblem_url": emblem_url,
            }
        except Exception as e:
            logging.warning("Skipping religion entry due to error: %s", e)
            continue
        body = (
            f"# Religion {fm['name']}\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"Culture → [[Cultures/Culture-{fm.get('culture', 0)}]]"
        )
        filename = f"Religion-{fm['religion_id']}-{safe_filename(fm['name'])}.md"
        path = os.path.join(VAULT_DIR, "Religions", filename)
        write_markdown(path, fm, body)

def process_features(features):
    if not isinstance(features, list):
        logging.warning("features is not a list; skipping feature processing")
        return
    for f in features[1:]:
        try:
            if not isinstance(f, dict):
                logging.warning("Skipping non-dict feature entry: %s", repr(f))
                continue
            emblem_url = get_emblem_for("feature", f, f.get("i", "unknown"))
            fm = {
                "feature_id": f.get("i", 0),
                "type": f.get("type", ""),
                "group": f.get("group", ""),
                "cells": f.get("cells", []),
                "emblem_url": emblem_url,
            }
        except Exception as e:
            logging.warning("Skipping feature entry due to error: %s", e)
            continue
        body = (
            f"# Feature {fm['feature_id']} ({fm.get('type','')})\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"Cells → {fm['cells']}"
        )
        filename = f"Feature-{fm['feature_id']}-{safe_filename(fm.get('type',''))}.md"
        path = os.path.join(VAULT_DIR, "Features", filename)
        write_markdown(path, fm, body)

def process_rivers(rivers):
    if not isinstance(rivers, list):
        logging.warning("rivers is not a list; skipping river processing")
        return
    for r in rivers:
        try:
            if not isinstance(r, dict):
                logging.warning("Skipping non-dict river entry: %s", repr(r))
                continue
            fm = {
                "river_id": r.get("i", 0),
                "name": r.get("name", ""),
                "source_cell": r.get("source", 0),
                "mouth_cell": r.get("mouth", 0),
                "basin": r.get("basin", 0),
                "cells": r.get("cells", []),
                "length_km": r.get("length", 0),
                "flux": r.get("discharge", 0),
            }
            body = (
                f"# River {fm['name']}\n"
                f"Flows through → {fm['cells']}\n"
                f"Mouth → [[Cells/Cell-{fm['mouth_cell']}]]"
            )
            filename = f"River-{fm['river_id']}-{safe_filename(fm['name'])}.md"
            path = os.path.join(VAULT_DIR, "Rivers", filename)
            write_markdown(path, fm, body)
        except Exception as e:
            logging.warning("Skipping river entry due to error: %s", e)
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert FMG map.json into an Obsidian-style World vault")
    parser.add_argument("mapfile", help="Path to FMG exported JSON (map.json)")
    parser.add_argument("--outdir", "-o", default="World", help="Output vault directory (default: World)")
    parser.add_argument("--download-emblems", action="store_true", help="Download emblem URLs (HTTP/HTTPS) instead of expecting local files")
    parser.add_argument("--mfcg-dir", default=None, help="Optional: directory containing Medieval Fantasy City Generator outputs to attach to matching Burgs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    # Configure runtime globals based on args
    VAULT_DIR = args.outdir
    EMBLEM_DIR = os.path.join(VAULT_DIR, "emblems")
    DOWNLOAD_EMBLEMS = args.download_emblems
    MFCG_DIR = args.mfcg_dir

    ensure_vault_dirs(VAULT_DIR)

    try:
        with open(args.mapfile, "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        logging.error("Failed to open map file %s: %s", args.mapfile, e)
        raise SystemExit(2)

    pack = data.get("pack")
    if not pack:
        logging.error("Input JSON does not contain top-level 'pack' key")
        raise SystemExit(2)

    process_cells(pack)
    process_burgs(pack.get("burgs", []))
    process_states(pack.get("states", []))
    process_provinces(pack.get("provinces", []))
    process_cultures(pack.get("cultures", []))
    process_religions(pack.get("religions", []))
    process_features(pack.get("features", []))
    process_rivers(pack.get("rivers", []))