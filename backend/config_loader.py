import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "backend/data"))


def _resolve_config(filename: str) -> Path:
    """Check volume path first, fall back to source tree."""
    volume_path = DATA_DIR / filename
    source_path = Path(__file__).parent.parent / "config" / filename
    return volume_path if volume_path.exists() else source_path
