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

# Default output vault directory (can be overridden by CLI)
VAULT_DIR = "World"
EMBLEM_DIR = os.path.join(VAULT_DIR, "emblems")
DOWNLOAD_EMBLEMS = False

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

def save_emblem_image(src_path, obj_type, obj_id, ext="png", download=False):
    filename = f"{obj_type}-{obj_id}.{ext}"
    dst_path = os.path.join(EMBLEM_DIR, filename)
    # If src_path is a URL and download allowed, attempt to download
    if isinstance(src_path, str) and src_path.startswith(("http://", "https://")):
        if not download:
            logging.warning("Emblem URL provided but --download-emblems not set: %s", src_path)
            return ""
        try:
            resp = requests.get(src_path, stream=True, timeout=10)
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

def process_cells(pack):
    cells = pack.get("cells", {})
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
            emblem_url = ""
            if "coa" in b and isinstance(b["coa"], dict) and "svg" in b["coa"]:
                emblem_url = save_emblem_svg("burg", b.get("i", "unknown"), b["coa"]["svg"])
            elif "emblem_url" in b:
                ext = str(b["emblem_url"]).split(".")[-1]
                emblem_url = save_emblem_image(b["emblem_url"], "burg", b.get("i", "unknown"), ext, download=DOWNLOAD_EMBLEMS)
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
        body = (
            f"# Burg {fm['name']}\n"
            f"{f'![Emblem]({fm['emblem_url']})' if fm['emblem_url'] else ''}\n"
            f"Located in [[Cells/Cell-{fm['cell']}]]\n"
            f"Culture → [[Cultures/Culture-{fm['culture']}]]\n"
            f"State → [[States/State-{fm['state']}]]\n"
            f"Feature → [[Features/Feature-{fm['feature']}]]"
        )
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
            emblem_url = ""
            if "coa" in s and isinstance(s["coa"], dict) and "svg" in s["coa"]:
                emblem_url = save_emblem_svg("state", s.get("i", "unknown"), s["coa"]["svg"])
            elif "emblem_url" in s:
                ext = str(s["emblem_url"]).split(".")[-1]
                emblem_url = save_emblem_image(s["emblem_url"], "state", s.get("i", "unknown"), ext, download=DOWNLOAD_EMBLEMS)
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
            emblem_url = ""
            if "coa" in p and isinstance(p["coa"], dict) and "svg" in p["coa"]:
                emblem_url = save_emblem_svg("province", p.get("i", "unknown"), p["coa"]["svg"])
            elif "emblem_url" in p:
                ext = str(p["emblem_url"]).split(".")[-1]
                emblem_url = save_emblem_image(p["emblem_url"], "province", p.get("i", "unknown"), ext, download=DOWNLOAD_EMBLEMS)
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
            emblem_url = ""
            if "coa" in c and isinstance(c["coa"], dict) and "svg" in c["coa"]:
                emblem_url = save_emblem_svg("culture", c.get("i", "unknown"), c["coa"]["svg"])
            elif "emblem_url" in c:
                ext = str(c["emblem_url"]).split(".")[-1]
                emblem_url = save_emblem_image(c["emblem_url"], "culture", c.get("i", "unknown"), ext, download=DOWNLOAD_EMBLEMS)
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
            emblem_url = ""
            if "coa" in r and isinstance(r["coa"], dict) and "svg" in r["coa"]:
                emblem_url = save_emblem_svg("religion", r.get("i", "unknown"), r["coa"]["svg"])
            elif "emblem_url" in r:
                ext = str(r["emblem_url"]).split(".")[-1]
                emblem_url = save_emblem_image(r["emblem_url"], "religion", r.get("i", "unknown"), ext, download=DOWNLOAD_EMBLEMS)
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
            emblem_url = ""
            if "coa" in f and isinstance(f["coa"], dict) and "svg" in f["coa"]:
                emblem_url = save_emblem_svg("feature", f.get("i", "unknown"), f["coa"]["svg"])
            elif "emblem_url" in f:
                ext = str(f["emblem_url"]).split(".")[-1]
                emblem_url = save_emblem_image(f["emblem_url"], "feature", f.get("i", "unknown"), ext, download=DOWNLOAD_EMBLEMS)
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
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    # Configure runtime globals based on args
    VAULT_DIR = args.outdir
    EMBLEM_DIR = os.path.join(VAULT_DIR, "emblems")
    DOWNLOAD_EMBLEMS = args.download_emblems

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