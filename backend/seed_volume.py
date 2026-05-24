"""
One-time seed script: copies pilot.db from the image into the persistent volume.
Run once after first deploy: railway run python backend/seed_volume.py
"""
import os
import shutil
import sys
from pathlib import Path

DST = Path(os.getenv("PILOT_DB_PATH", "/data/pilot.db"))

SOURCES = [
    Path("/app/backend/data/pilot.db"),
    Path("backend/data/pilot.db"),
]


def main():
    if DST.exists():
        size_mb = DST.stat().st_size / 1_000_000
        print(f"pilot.db already present at {DST} ({size_mb:.1f} MB). Skipping.")
        return

    src = next((p for p in SOURCES if p.exists()), None)
    if src is None:
        print(
            "ERROR: pilot.db not found in image. Ensure it is present at "
            "backend/data/pilot.db and that the Docker image was built with it."
        )
        sys.exit(1)

    size_mb = src.stat().st_size / 1_000_000
    print(f"Copying {src} → {DST} ({size_mb:.1f} MB)...")
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DST)
    print("Seed complete.")


if __name__ == "__main__":
    main()
