"""Loads train-hop credentials from a per-user env file into os.environ.

Location: `~/.mozbuild/trainhop.env` — Firefox's per-user directory, so it
needs nothing but a working local Firefox, lives outside every repo
(credentials can't be committed), and survives plugin updates.

Real environment variables always take precedence — the file only fills in
what is not already set. No third-party dependency (python-dotenv) required.
"""

import os
from pathlib import Path


def env_file_path():
    """Return the credentials file path (it may or may not exist)."""
    return Path.home() / ".mozbuild" / "trainhop.env"


def load_env():
    """Populate os.environ from the credentials file, if it exists."""
    path = env_file_path()
    if path.is_file():
        _load_file(path)


def _load_file(path):
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Skip empty values so a stray `KEY=` line doesn't shadow a real one
        # later in the file. Real environment variables take precedence.
        if key and value and key not in os.environ:
            os.environ[key] = value
