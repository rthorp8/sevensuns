import os
import shutil
from pathlib import Path

import pytest

from fmg_to_obsidian_Version3 import integrate_mfcg_assets, safe_filename


def make_file(path: Path, content: str = "x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_integrate_mfcg_copies_directory(tmp_path):
    # Setup sample MFCG root with a matching directory name Burg-2-Testburg
    mfcg_root = tmp_path / "mfcg_root"
    src_dir = mfcg_root / "Burg-2-Testburg"
    idx = src_dir / "index.html"
    make_file(idx, "<html>test</html>")

    # outdir (vault) where the integration will copy into
    vault = tmp_path / "vault"

    copied = integrate_mfcg_assets(2, "Testburg", str(mfcg_root), str(vault))

    # Expect at least one similar vault-relative path to the copied index.html
    assert copied, "Expected some files to be copied"
    # verify the file exists under the expected per-burg mfcg folder
    dest = vault / "Burgs" / f"Burg-2-{safe_filename('Testburg')}" / "mfcg" / "Burg-2-Testburg" / "index.html"
    assert dest.exists()


def test_integrate_mfcg_copies_files_if_no_dir_match(tmp_path):
    mfcg_root = tmp_path / "mfcg_root"
    # create a file matching the burg id in the root
    file_a = mfcg_root / "burg-3-scene.png"
    make_file(file_a, "PNG")

    vault = tmp_path / "vault"

    copied = integrate_mfcg_assets(3, "Scenetown", str(mfcg_root), str(vault))

    assert copied
    # copied file should appear in the per-burg mfcg folder
    dest = vault / "Burgs" / f"Burg-3-{safe_filename('Scenetown')}" / "mfcg" / "burg-3-scene.png"
    assert dest.exists()


def test_integrate_mfcg_copies_nested_directories(tmp_path):
    mfcg_root = tmp_path / "mfcg_root"
    src_dir = mfcg_root / "Burg-4-NestedTown"
    # create nested structure
    (src_dir / "assets" / "css").mkdir(parents=True)
    make_file(src_dir / "assets" / "css" / "style.css", "body{}")
    make_file(src_dir / "assets" / "img" / "map.png", "PNG")

    vault = tmp_path / "vault"

    copied = integrate_mfcg_assets(4, "Nested Town", str(mfcg_root), str(vault))

    # verify nested files exist in the destination
    dest_css = vault / "Burgs" / f"Burg-4-{safe_filename('Nested Town')}" / "mfcg" / "Burg-4-NestedTown" / "assets" / "css" / "style.css"
    dest_img = vault / "Burgs" / f"Burg-4-{safe_filename('Nested Town')}" / "mfcg" / "Burg-4-NestedTown" / "assets" / "img" / "map.png"
    assert dest_css.exists()
    assert dest_img.exists()


def test_integrate_mfcg_multiple_matches_and_files(tmp_path):
    # create a folder and a root-level file both matching the same burg
    mfcg_root = tmp_path / "mfcg_root"
    folder = mfcg_root / "Stonehaven_files"
    make_file(folder / "a.txt", "a")
    make_file(mfcg_root / "Burg-5-extra.txt", "b")

    vault = tmp_path / "vault"
    copied = integrate_mfcg_assets(5, "Stonehaven", str(mfcg_root), str(vault))

    # both should be copied into the per-burg mfcg folder
    dest1 = vault / "Burgs" / f"Burg-5-{safe_filename('Stonehaven')}" / "mfcg" / "Stonehaven_files" / "a.txt"
    dest2 = vault / "Burgs" / f"Burg-5-{safe_filename('Stonehaven')}" / "mfcg" / "Burg-5-extra.txt"
    assert dest1.exists()
    assert dest2.exists()


def test_integrate_mfcg_handles_special_character_names(tmp_path):
    # burg name with spaces and special chars
    mfcg_root = tmp_path / "mfcg_root"
    make_file(mfcg_root / "Burg-6-Köln@Town" / "index.html", "x")
    vault = tmp_path / "vault"
    copied = integrate_mfcg_assets(6, "Köln@Town", str(mfcg_root), str(vault))
    # safe_filename should be used in the destination path
    dest = vault / "Burgs" / f"Burg-6-{safe_filename('Köln@Town')}" / "mfcg" / "Burg-6-Köln@Town" / "index.html"
    assert dest.exists()


def test_integrate_mfcg_returns_empty_for_missing_root(tmp_path):
    # Non-existent root should just return an empty list
    vault = tmp_path / "vault"
    copied = integrate_mfcg_assets(99, "Nope", str(tmp_path / 'no_exist_root'), str(vault))
    assert copied == []
