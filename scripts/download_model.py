#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

MODEL_ID = "zai-org/GLM-5.3"
FALLBACK_REQUIRED_BYTES = 800 * 1024**3


def human_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return str(value)


def estimate_required_bytes() -> int:
    info = HfApi().model_info(MODEL_ID, files_metadata=True)
    sizes = [
        sibling.size
        for sibling in (info.siblings or [])
        if getattr(sibling, "size", None) is not None
    ]
    reported = sum(sizes)
    if reported <= 0:
        return FALLBACK_REQUIRED_BYTES

    # Add headroom for temporary files and filesystem overhead.
    return max(int(reported * 1.10), FALLBACK_REQUIRED_BYTES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the official Z.ai GLM-5.3 snapshot from Hugging Face."
    )
    parser.add_argument(
        "--local-dir",
        default="./models/GLM-5.3",
        help="Destination directory (default: ./models/GLM-5.3)",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Hugging Face revision to download (default: main)",
    )
    parser.add_argument(
        "--confirm-large-download",
        action="store_true",
        help="Required safety switch acknowledging the very large download.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_large_download:
        raise SystemExit(
            "Refusing to start a hundreds-of-GB download. "
            "Re-run with --confirm-large-download after checking storage and bandwidth."
        )

    destination = Path(args.local_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    required = estimate_required_bytes()
    free = shutil.disk_usage(destination).free
    print(f"Estimated required free space: {human_bytes(required)}")
    print(f"Available free space:          {human_bytes(free)}")

    if free < required:
        raise SystemExit(
            "Insufficient free disk space for a safe full snapshot download."
        )

    path = snapshot_download(
        repo_id=MODEL_ID,
        revision=args.revision,
        local_dir=str(destination),
    )
    print(f"Downloaded official snapshot to: {path}")


if __name__ == "__main__":
    main()
