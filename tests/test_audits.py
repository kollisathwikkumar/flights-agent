"""Audit tests for API key security and absence of runtime fake data."""

import os
from pathlib import Path
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "notebook"}
CODE_EXTENSIONS = {".py", ".sh"}


def get_all_source_files():
    source_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            p = Path(root) / f
            if p.suffix in CODE_EXTENSIONS and "test_audits.py" not in p.name:
                source_files.append(p)
    return source_files


def test_audit_no_hardcoded_api_keys():
    """TEST 24: Verify that no raw API key values are hardcoded in source code."""
    env_vals = dotenv_values(BASE_DIR / ".env")
    prohibited_keys = [v.strip() for v in env_vals.values() if len(v.strip()) > 10 and not v.startswith("http") and not v.startswith("meta/")]

    source_files = get_all_source_files()
    for file_path in source_files:
        content = file_path.read_text(encoding="utf-8")
        for key in prohibited_keys:
            assert key not in content, f"Hardcoded API key found in source file {file_path.relative_to(BASE_DIR)}"


def test_audit_no_runtime_fake_data():
    """TEST 23: Verify that runtime code does not contain fake flight/fare databases."""
    prohibited_phrases = [
        "mock price",
        "fake price",
        "synthetic fare",
        "fake flight",
        "datasets/flight-fares",
        "Public Flight Fare Portal",
    ]

    source_files = get_all_source_files()
    for file_path in source_files:
        if "test_" in file_path.name:
            continue
        content = file_path.read_text(encoding="utf-8").lower()
        for phrase in prohibited_phrases:
            assert phrase not in content, f"Prohibited fake data reference '{phrase}' found in {file_path.relative_to(BASE_DIR)}"
