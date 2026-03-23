"""
Shared utilities for the Personalized Podcast pipeline.

This module is the "toolbox" that all other scripts reach into. It handles:
- Loading your config file (config.yaml)
- Loading your secret API keys (.env file)
- Setting up logging so you can see what's happening
- Reading/writing pipeline state (what was last processed)
- Finding the right directories for everything
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

DATA_DIR_ENV_VAR = "PODCAST_DATA_DIR"


def get_repo_root():
    """Returns the repository root directory."""
    return Path(__file__).resolve().parent.parent


def _legacy_data_dir(home_dir=None):
    """Returns the original legacy data directory path."""
    home = Path(home_dir) if home_dir is not None else Path.home()
    return home / ".claude" / "personalized-podcast"


def _looks_like_repo_data_dir(repo_root):
    """
    Detects repos that already store podcast state/assets at the project root.
    """
    repo_root = Path(repo_root)
    markers = ["episodes", "feed.xml", "episodes.json", "state.json"]
    return any((repo_root / marker).exists() for marker in markers)


def _ensure_data_subdirs(data_dir):
    """Creates the subdirectories required by the pipeline."""
    data_dir = Path(data_dir)
    for subdir in ["logs", "scripts_output", "episodes"]:
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)
    return data_dir


def _candidate_paths(filename, data_dir, repo_root, home_dir):
    """
    Builds an ordered list of possible file locations, preferring the selected
    data directory but still allowing fallback to the legacy home path.
    """
    candidates = []
    seen = set()

    for base in [
        Path(data_dir),
        Path(repo_root),
        _legacy_data_dir(home_dir),
    ]:
        candidate = base / filename
        if candidate not in seen:
            candidates.append(candidate)
            seen.add(candidate)

    return candidates


def get_data_dir(data_dir=None, repo_root=None, home_dir=None):
    """
    Returns the active pipeline data directory and creates required subdirs.

    Resolution order:
    1. Explicit data_dir argument
    2. PODCAST_DATA_DIR environment variable
    3. Repo root, if this repo already stores podcast artifacts in-project
    4. Legacy ~/.claude/personalized-podcast path
    """
    repo_root = Path(repo_root) if repo_root is not None else get_repo_root()

    if data_dir is not None:
        chosen_dir = Path(data_dir).expanduser()
    else:
        env_dir = os.environ.get(DATA_DIR_ENV_VAR)
        if env_dir:
            chosen_dir = Path(env_dir).expanduser()
        elif _looks_like_repo_data_dir(repo_root):
            chosen_dir = repo_root
        else:
            chosen_dir = _legacy_data_dir(home_dir)

    try:
        return _ensure_data_subdirs(chosen_dir)
    except PermissionError:
        if chosen_dir == repo_root:
            raise
        return _ensure_data_subdirs(repo_root)


def load_config(config_path=None, data_dir=None, repo_root=None, home_dir=None):
    """
    Reads your config.yaml file and returns it as a Python dictionary.

    If no path is given, looks in the default location:
    - PODCAST_DATA_DIR/config.yaml when set
    - repo_root/config.yaml for repo-local setups
    - ~/.claude/personalized-podcast/config.yaml for legacy setups

    Raises a helpful error if the file is missing, so you know
    exactly what to do to fix it.
    """
    if config_path is None:
        repo_root = Path(repo_root) if repo_root is not None else get_repo_root()
        data_dir = get_data_dir(
            data_dir=data_dir,
            repo_root=repo_root,
            home_dir=home_dir,
        )
        candidates = _candidate_paths("config.yaml", data_dir, repo_root, home_dir)
        config_path = next((path for path in candidates if path.exists()), candidates[0])
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}\n\n"
            f"Create it at {config_path} or copy config.example.yaml into place. "
            f"See the README for the full config reference:\n"
            f"  https://github.com/TMFNK/my-podcast-feed#setup"
        )

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def load_env(env_path=None, data_dir=None, repo_root=None, home_dir=None):
    """
    Loads your .env file (which contains API keys) into the environment.

    The .env file keeps your secrets separate from the config file,
    so you never accidentally share them. It loads them as environment
    variables that the API libraries can find automatically.
    """
    if env_path is None:
        repo_root = Path(repo_root) if repo_root is not None else get_repo_root()
        data_dir = get_data_dir(
            data_dir=data_dir,
            repo_root=repo_root,
            home_dir=home_dir,
        )
        candidates = _candidate_paths(".env", data_dir, repo_root, home_dir)
        env_path = next((path for path in candidates if path.exists()), candidates[0])
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        raise FileNotFoundError(
            f"Environment file not found at {env_path}\n"
            f"Create it with your API keys:\n"
            f"  OPENAI_API_KEY=...\n"
        )

    load_dotenv(env_path)


def setup_logging(log_dir=None):
    """
    Sets up logging so every pipeline run creates a log file.

    Logs go to two places:
    1. A file: ~/.claude/personalized-podcast/logs/YYYY-MM-DD.log
    2. The terminal (stdout) so you can watch in real time

    Returns a logger object that all scripts use to record what they're doing.
    """
    if log_dir is None:
        log_dir = get_data_dir() / "logs"

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # One log file per day
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    # Create a logger with a descriptive name
    logger = logging.getLogger("personalized-podcast")
    logger.setLevel(logging.DEBUG)

    # Don't add duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # File handler — captures everything for debugging later
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # Console handler — shows progress in real time
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def read_state(state_path=None):
    """
    Reads the pipeline's state file to know what was last processed.

    The state tracks:
    - last_run: when the pipeline last ran (ISO timestamp)
    - processed_ids: IDs of articles already turned into episodes

    If the state file doesn't exist yet (first run), returns empty defaults.
    """
    if state_path is None:
        state_path = get_data_dir() / "state.json"
    else:
        state_path = Path(state_path)

    if not state_path.exists():
        return {"last_run": None, "processed_ids": []}

    with open(state_path, "r") as f:
        return json.load(f)


def write_state(state, state_path=None):
    """
    Saves the pipeline's state to disk.

    Uses an "atomic write" pattern: writes to a temporary file first,
    then renames it. This prevents corruption if the process crashes
    mid-write — you either get the old state or the new state, never
    a half-written mess.
    """
    if state_path is None:
        state_path = get_data_dir() / "state.json"
    else:
        state_path = Path(state_path)

    # Write to a temp file in the same directory, then rename
    # (rename is atomic on the same filesystem)
    tmp_path = state_path.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2)
    tmp_path.rename(state_path)
