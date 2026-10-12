"""
make_zip.py — create DocuSense_IBM_SkillsBuild_2026.zip in the parent directory.

Excludes: .venv, data/raw, data/processed, __pycache__, .pytest_cache,
          .mypy_cache, .idea, .vscode, *.db, *.joblib, *.log, *.zip, *.pyc, *.pyo
"""

import os
import sys
import zipfile
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent   # DocuSense/
OUT_ZIP   = REPO_ROOT.parent / "DocuSense_IBM_SkillsBuild_2026.zip"

SKIP_DIRS = {
    ".venv", "venv", "env",
    "data", "raw", "processed",          # skip all of data/ then allow data/ files below
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".idea", ".vscode", ".agents", ".gemini",
    "playwright-browsers", "node_modules",
    "dist", "build",
}
SKIP_EXT = {".db", ".joblib", ".log", ".pyc", ".pyo", ".zip"}
# data/ sub-paths we want to KEEP
KEEP_DATA_PATTERNS = ["data/README.md", "data/synthetic/"]

def include(path: pathlib.Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    parts = list(rel.parts)

    # Skip top-level dirs that are in SKIP_DIRS
    if parts[0] in SKIP_DIRS:
        # Allow data/README.md and data/synthetic/
        rel_str = str(rel).replace("\\", "/")
        if any(rel_str.startswith(p) or rel_str == p.rstrip("/") for p in KEEP_DATA_PATTERNS):
            return True
        return False

    # Any intermediate dir named in SKIP_DIRS?
    for part in parts[:-1]:
        if part in SKIP_DIRS:
            return False

    # Extension filter for files
    if path.is_file() and path.suffix.lower() in SKIP_EXT:
        return False

    return True

files = [p for p in REPO_ROOT.rglob("*") if p.is_file() and include(p)]
print(f"Packing {len(files)} files to {OUT_ZIP}")

with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for f in sorted(files):
        arcname = "DocuSense/" + str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        zf.write(f, arcname)

size_mb = OUT_ZIP.stat().st_size / 1_048_576
print(f"Done!  {OUT_ZIP}  ({size_mb:.1f} MB)  —  {len(files)} files")
