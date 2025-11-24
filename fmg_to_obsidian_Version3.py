import json
import os
import shutil

VAULT_DIR = "World"
EMBLEM_DIR = os.path.join(VAULT_DIR, "emblems")

# Ensure folders exist 
folders = [
    "Cells", "Burgs", "States", "Provinces",
    "Cultures", "Religions", "Features", "Rivers", "emblems"
]
for folder in folders:
    os.makedirs(os.path.join(VAULT_DIR, folder), exist_ok=True)

def write_markdown(path, frontmatter, body):
    """Write a Markdown file with YAML frontmatter + body."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        for k, v in frontmatter.items():
            # Use repr to properly encode dictionaries and lists
            f.write(f"{k}: {repr(v)}\n")
        f.write("---\n\n")
        f.write(body)

def save_emblem_svg(obj_type, obj_id, svg_data):
    filename = f"{obj_type}-{obj_id}.svg"
    path = os.path.join(EMBLEM_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_data)
    return f"emblems/{filename}"

def save_emblem_image(src_path, obj_type, obj_id, ext="png"):
    filename = f"{obj_type}-{obj_id}.{ext}"
    dst_path = os.path.join(EMBLEM_DIR, filename)
    shutil.copy(src_path, dst_path)
    return f"emblems/{filename}"

def process_cells(pack):
    for cid, elev in enumerate(pack["cells"]["h"]):
        fm = {
            "cell_id": cid,
            "x": float(pack["cells"].get("x", [0]*len(pack["cells"]["h"]))[cid]),
            "y": float(pack["cells"].get("y", [0]*len(pack["cells"]["h"]))[cid]),
            "elevation": int(elev),
            "feature": int(pack["cells"]["f"][cid]),
            "biome": int(pack["cells"]["biome"][cid]),
            "burg": int(pack["cells"]["burg"][cid]),
            "culture": int(pack["cells"]["culture"][cid]),
            "state": int(pack["cells"]["state"][cid]),
            "province": int(pack["cells"]["province"][cid]),
            "religion": int(pack["cells"]["religion"][cid]),
            "population": float(pack["cells"]["pop"][cid]),
            "river": int(pack["cells"]["r"][cid]),
            "flux": int(pack["cells"]["fl"][cid]),
            "harbor_score": int(pack["cells"]["harbor"][cid]),
            "routes": pack["cells"].get("routes", {}).get(cid, {}),
        }
        body = (
            f"# Cell {cid}\n"
            f"Links → [[Features/Feature-{fm['feature']}]], "
            f"[[Cultures/Culture-{fm['culture']}]], [[States/State-{fm['state']}]], "
            f"[[Provinces/Province-{fm['province']}]], [[Religions/Religion-{fm['religion']}]], "
            f"[[Rivers/River-{fm['river']}]], [[Burgs/Burg-{fm['burg']}]]"
        )
        path = os.path.join(VAULT_DIR, "Cells", f"Cell-{cid}.md")
        write_markdown(path, fm, body)

def process_burgs(burgs):
    for b in burgs[1:]:  # skip element 0
        emblem_url = ""
        if "coa" in b and isinstance(b["coa"], dict) and "svg" in b["coa"]:
            emblem_url = save_emblem_svg("burg", b["i"], b["coa"]["svg"])
        elif "emblem_url" in b:
            ext = b["emblem_url"].split(".")[-1]
            emblem_url = save_emblem_image(b["emblem_url"], "burg", b["i"], ext)
        fm = {
            "burg_id": b["i"],
            "name": b["name"],
            "cell": b["cell"],
            "culture": b["culture"],
            "state": b["state"],
            "feature": b["feature"],
            "population": b["population"],
            "type": b["type"],
            "capital": b["capital"],
            "port": b["port"],
            "citadel": b["citadel"],
            "plaza": b["plaza"],
            "temple": b["temple"],
            "walls": b["walls"],
            "emblem_url": emblem_url,
        }
        body = (
            f"# Burg {b['name']}\n"
            f"{f'![Emblem]({emblem_url})' if emblem_url else ''}\n"
            f"Located in [[Cells/Cell-{b['cell']}]]\n"
            f"Culture → [[Cultures/Culture-{b['culture']}]]\n"
            f"State → [[States/State-{b['state']}]]\n"
            f"Feature → [[Features/Feature-{b['feature']}]]"
        )
        path = os.path.join(VAULT_DIR, "Burgs", f"Burg-{b['i']}-{b['name'].replace(' ', '_')}.md")
        write_markdown(path, fm, body)

def process_states(states):
    for s in states[1:]:
        emblem_url = ""
        if "coa" in s and isinstance(s["coa"], dict) and "svg" in s["coa"]:
            emblem_url = save_emblem_svg("state", s["i"], s["coa"]["svg"])
        elif "emblem_url" in s:
            ext = s["emblem_url"].split(".")[-1]
            emblem_url = save_emblem_image(s["emblem_url"], "state", s["i"], ext)
        fm = {
            "state_id": s["i"],
            "name": s["name"],
            "form": s.get("form", ""),
            "culture": s["culture"],
            "capital_burg": s.get("capital", 0),
            "provinces": s.get("provinces", []),
            "neighbors": s.get("neighbors", []),
            "burgs": s.get("burgs", []),
            "emblem_url": emblem_url,
        }
        body = (
            f"# State {s['name']}\n"
            f"{f'![Emblem]({emblem_url})' if emblem_url else ''}\n"
            f"Culture → [[Cultures/Culture-{s['culture']}]]\n"
            f"Capital → [[Burgs/Burg-{fm['capital_burg']}]]"
        )
        path = os.path.join(VAULT_DIR, "States", f"State-{s['i']}-{s['name'].replace(' ', '_')}.md")
        write_markdown(path, fm, body)

def process_provinces(provinces):
    for p in provinces[1:]:
        emblem_url = ""
        if "coa" in p and isinstance(p["coa"], dict) and "svg" in p["coa"]:
            emblem_url = save_emblem_svg("province", p["i"], p["coa"]["svg"])
        elif "emblem_url" in p:
            ext = p["emblem_url"].split(".")[-1]
            emblem_url = save_emblem_image(p["emblem_url"], "province", p["i"], ext)
        fm = {
            "province_id": p["i"],
            "name": p["name"],
            "state": p["state"],
            "capital_burg": p.get("burg", 0),
            "burgs": p.get("burgs", []),
            "cells": p.get("cells", []),
            "emblem_url": emblem_url,
        }
        body = (
            f"# Province {p['name']}\n"
            f"{f'![Emblem]({emblem_url})' if emblem_url else ''}\n"
            f"State → [[States/State-{p['state']}]]\n"
            f"Capital → [[Burgs/Burg-{fm['capital_burg']}]]"
        )
        path = os.path.join(VAULT_DIR, "Provinces", f"Province-{p['i']}-{p['name'].replace(' ', '_')}.md")
        write_markdown(path, fm, body)

def process_cultures(cultures):
    for c in cultures[1:]:
        emblem_url = ""
        if "coa" in c and isinstance(c["coa"], dict) and "svg" in c["coa"]:
            emblem_url = save_emblem_svg("culture", c["i"], c["coa"]["svg"])
        elif "emblem_url" in c:
            ext = c["emblem_url"].split(".")[-1]
            emblem_url = save_emblem_image(c["emblem_url"], "culture", c["i"], ext)
        fm = {
            "culture_id": c["i"],
            "name": c["name"],
            "origins": c.get("origins", []),
            "states": [],
            "burgs": [],
            "color": c.get("color", ""),
            "expansionism": c.get("expansionism", 1.0),
            "emblem_url": emblem_url,
        }
        body = (
            f"# Culture {c['name']}\n"
            f"{f'![Emblem]({emblem_url})' if emblem_url else ''}\n"
            f"Origins → {fm['origins']}"
        )
        path = os.path.join(VAULT_DIR, "Cultures", f"Culture-{c['i']}-{c['name'].replace(' ', '_')}.md")
        write_markdown(path, fm, body)

def process_religions(religions):
    for r in religions[1:]:
        emblem_url = ""
        if "coa" in r and isinstance(r["coa"], dict) and "svg" in r["coa"]:
            emblem_url = save_emblem_svg("religion", r["i"], r["coa"]["svg"])
        elif "emblem_url" in r:
            ext = r["emblem_url"].split(".")[-1]
            emblem_url = save_emblem_image(r["emblem_url"], "religion", r["i"], ext)
        fm = {
            "religion_id": r["i"],
            "name": r["name"],
            "type": r.get("type", ""),
            "deity": r.get("deity", ""),
            "culture": r.get("culture", 0),
            "states": [],
            "cells": [],
            "emblem_url": emblem_url,
        }
        body = (
            f"# Religion {r['name']}\n"
            f"{f'![Emblem]({emblem_url})' if emblem_url else ''}\n"
            f"Culture → [[Cultures/Culture-{r.get('culture', 0)}]]"
        )
        path = os.path.join(VAULT_DIR, "Religions", f"Religion-{r['i']}-{r['name'].replace(' ', '_')}.md")
        write_markdown(path, fm, body)

def process_features(features):
    for f in features[1:]:
        emblem_url = ""
        if "coa" in f and isinstance(f["coa"], dict) and "svg" in f["coa"]:
            emblem_url = save_emblem_svg("feature", f["i"], f["coa"]["svg"])
        elif "emblem_url" in f:
            ext = f["emblem_url"].split(".")[-1]
            emblem_url = save_emblem_image(f["emblem_url"], "feature", f["i"], ext)
        fm = {
            "feature_id": f["i"],
            "type": f.get("type", ""),
            "group": f.get("group", ""),
            "cells": f.get("cells", []),
            "emblem_url": emblem_url,
        }
        body = (
            f"# Feature {f['i']} ({f.get('type','')})\n"
            f"{f'![Emblem]({emblem_url})' if emblem_url else ''}\n"
            f"Cells → {fm['cells']}"
        )
        path = os.path.join(VAULT_DIR, "Features", f"Feature-{f['i']}-{f.get('type','').replace(' ', '_')}.md")
        write_markdown(path, fm, body)

def process_rivers(rivers):
    for r in rivers:
        fm = {
            "river_id": r["i"],
            "name": r["name"],
            "source_cell": r.get("source", 0),
            "mouth_cell": r.get("mouth", 0),
            "basin": r.get("basin", 0),
            "cells": r.get("cells", []),
            "length_km": r.get("length", 0),
            "flux": r.get("discharge", 0),
        }
        body = (
            f"# River {r['name']}\n"
            f"Flows through → {fm['cells']}\n"
            f"Mouth → [[Cells/Cell-{fm['mouth_cell']}]]"
        )
        path = os.path.join(VAULT_DIR, "Rivers", f"River-{r['i']}-{r['name'].replace(' ', '_')}.md")
        write_markdown(path, fm, body)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fmg_to_obsidian.py map.json")
        exit(1)
    mapfile = sys.argv[1]
    with open(mapfile, "r", encoding="utf-8") as f:
        data = json.load(f)
    process_cells(data["pack"])
    process_burgs(data["pack"]["burgs"])
    process_states(data["pack"]["states"])
    process_provinces(data["pack"]["provinces"])
    process_cultures(data["pack"]["cultures"])
    process_religions(data["pack"]["religions"])
    process_features(data["pack"]["features"])
    process_rivers(data["pack"]["rivers"])