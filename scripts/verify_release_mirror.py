#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi

MODEL_ID = "zai-org/GLM-5.3"


def get_sha256(sibling: Any) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    if isinstance(lfs, dict):
        return lfs.get("sha256")
    if lfs is not None:
        return getattr(lfs, "sha256", None)
    return None


def parse_assets(path: Path) -> dict[str, int]:
    assets: dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue
            name, size = row[0], row[1]
            assets[name] = int(size)
    return assets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    parser.add_argument("--assets-tsv", required=True)
    parser.add_argument("--manifests-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api = HfApi()
    info = api.model_info(
        MODEL_ID,
        revision=args.revision,
        files_metadata=True,
    )
    if info.sha != args.revision:
        raise SystemExit(
            f"Revision mismatch: requested {args.revision}, resolved {info.sha}"
        )

    siblings = sorted(info.siblings or [], key=lambda item: item.rfilename)
    expected = {item.rfilename: item for item in siblings}
    assets = parse_assets(Path(args.assets_tsv))

    manifests_dir = Path(args.manifests_dir)
    manifests = sorted(manifests_dir.glob("manifest-*.json"))
    entries: dict[str, dict[str, Any]] = {}
    duplicate_paths: list[str] = []

    for manifest_path in manifests:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("model_id") != MODEL_ID:
            raise SystemExit(f"Wrong model ID in {manifest_path}")
        if data.get("revision") != args.revision:
            raise SystemExit(f"Wrong revision in {manifest_path}")
        for entry in data.get("files", []):
            path = entry["path"]
            if path in entries:
                duplicate_paths.append(path)
            entries[path] = entry

    if duplicate_paths:
        raise SystemExit(
            "Duplicate mirrored paths: " + ", ".join(sorted(set(duplicate_paths)))
        )

    missing_paths = sorted(
        path for path in expected if path != "LICENSE" and path not in entries
    )
    unexpected_paths = sorted(path for path in entries if path not in expected)
    if missing_paths:
        raise SystemExit(
            f"Missing {len(missing_paths)} upstream files: "
            + ", ".join(missing_paths[:20])
        )
    if unexpected_paths:
        raise SystemExit(
            f"Unexpected mirrored files: {', '.join(unexpected_paths[:20])}"
        )

    license_info = expected.get("LICENSE")
    if license_info is None:
        raise SystemExit("Upstream LICENSE is missing")
    if "LICENSE" not in assets:
        raise SystemExit("GitHub Release does not contain LICENSE")
    if getattr(license_info, "size", None) is not None:
        if assets["LICENSE"] != license_info.size:
            raise SystemExit(
                f"LICENSE size mismatch: expected {license_info.size}, "
                f"got {assets['LICENSE']}"
            )

    verified_bytes = assets["LICENSE"]
    verified_files = 1
    verified_parts = 0

    for path, sibling in expected.items():
        if path == "LICENSE":
            continue

        entry = entries[path]
        expected_size = getattr(sibling, "size", None)
        if expected_size is not None and entry["size"] != expected_size:
            raise SystemExit(
                f"Size mismatch for {path}: expected {expected_size}, "
                f"manifest has {entry['size']}"
            )

        upstream_sha = get_sha256(sibling)
        if upstream_sha:
            if entry.get("upstream_sha256") != upstream_sha:
                raise SystemExit(f"Upstream digest metadata mismatch for {path}")
            if entry.get("sha256") != upstream_sha:
                raise SystemExit(f"Content SHA-256 mismatch for {path}")

        part_total = 0
        for part in entry["parts"]:
            name = part["name"]
            size = int(part["size"])
            if name not in assets:
                raise SystemExit(f"Missing release asset {name} for {path}")
            if assets[name] != size:
                raise SystemExit(
                    f"Release asset size mismatch for {name}: "
                    f"manifest {size}, release {assets[name]}"
                )
            part_total += size
            verified_parts += 1

        if part_total != entry["size"]:
            raise SystemExit(
                f"Part total mismatch for {path}: {part_total} != {entry['size']}"
            )

        verified_bytes += entry["size"]
        verified_files += 1

    result = {
        "status": "complete",
        "model_id": MODEL_ID,
        "revision": args.revision,
        "upstream_file_count": len(expected),
        "verified_file_count": verified_files,
        "verified_part_count": verified_parts,
        "verified_bytes": verified_bytes,
        "release_asset_count": len(assets),
        "license_present": True,
        "verification": {
            "all_upstream_paths_present": True,
            "release_part_sizes_match": True,
            "upstream_sha256_checked_where_available": True,
        },
    }

    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
