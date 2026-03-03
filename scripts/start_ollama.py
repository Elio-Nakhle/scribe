#!/usr/bin/env python3
"""
Start Ollama via Docker Compose and ensure a small default model is pulled (runs in ~1GB).
Use: pdm run ollama
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

COMPOSE_SERVICE = "ollama"
OLLAMA_API = "http://localhost:11434"
DEFAULT_MODEL = "tinyllama"  # ~637MB; use --model gemma2 etc. if you have more memory
MAX_WAIT_SECONDS = 60


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ollama_ready() -> bool:
    try:
        req = urllib.request.Request(f"{OLLAMA_API}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as _:
            return True
    except Exception:
        return False


def main() -> int:
    root = project_root()
    compose_file = root / "docker-compose.yml"
    if not compose_file.exists():
        print("docker-compose.yml not found.", file=sys.stderr)
        return 1

    print("Starting Ollama (Docker Compose)...")
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode
    print("Waiting for Ollama to be ready...")
    for _ in range(MAX_WAIT_SECONDS):
        if ollama_ready():
            break
        time.sleep(1)
    else:
        print("Ollama did not become ready in time.", file=sys.stderr)
        return 1
    print(f"Pulling model {DEFAULT_MODEL} (if not already present)...")
    pull = subprocess.run(
        [
            "docker-compose",
            "exec",
            "-T",
            COMPOSE_SERVICE,
            "ollama",
            "pull",
            DEFAULT_MODEL,
        ],
        cwd=root,
    )
    if pull.returncode != 0:
        return pull.returncode
    print(f"Ollama is running. Use: pdm run summary (default {DEFAULT_MODEL}) or --model <name>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
