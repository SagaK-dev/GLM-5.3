#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import requests
from huggingface_hub import HfApi, hf_hub_url

MODEL_ID = "zai-org/GLM-5.3"
PART_SIZE = 1_900_000_000
BUFFER_SIZE = 8 * 1024 * 1024


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def asset_name(path: str, part: int | None = None) -> str:
    safe = path.replace("/", "__")
    if part is None:
        return safe
    return f"{safe}.part{part:04d}"


def get_sha256(sibling: Any) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    if isinstance(lfs, dict):
        return lfs.get("sha256")
    if lfs is not None:
        return getattr(lfs, "sha256", None)
    return None


def upload(tag: str, path: Path) -> None:
    run("gh", "release", "upload", tag, str(path), "--clobber")


def ensure_release(tag: str, revision: str) -> None:
    result = subprocess.run(
        ["gh", "release", "view", tag],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return
    run(
        "gh",
        "release",
        "create",
        tag,
        "--title",
        f"GLM-5.3 upstream mirror {revision[:12]}",
        "--notes",
        (
            "Byte-preserving mirror assets for the official zai-org/GLM-5.3 "
            f"revision {revision}. Large files are split into <1.9 GB parts. "
            "The official upstream LICENSE is included as a release asset. "
            "See MIRRORING.md and the uploaded manifests."
        ),
    )


def ensure_upstream_license(tag: str, revision: str) -> None:
    url = hf_hub_url(repo_id=MODEL_ID, filename="LICENSE", revision=revision)
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with tempfile.TemporaryDirectory(prefix="glm53-license-") as tmp:
            path = Path(tmp) / "LICENSE"
            with path.open("wb") as out:
                for chunk in response.iter_content(chunk_size=BUFFER_SIZE):
                    if chunk:
                        out.write(chunk)
            upload(tag, path)


def stream_one(
    *,
    path: str,
    revision: str,
    tag: str,
    expected_size: int | None,
    expected_sha256: str | None,
) -> dict[str, Any]:
    url = hf_hub_url(repo_id=MODEL_ID, filename=path, revision=revision)
    full_hash = hashlib.sha256()
    total = 0
    parts: list[dict[str, Any]] = []

    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()

        with tempfile.TemporaryDirectory(prefix="glm53-mirror-") as tmp:
            tmpdir = Path(tmp)
            part_no = 1
            current_name = asset_name(path, part_no)
            current_path = tmpdir / current_name
            current = current_path.open("wb")
            current_size = 0

            try:
                for chunk in response.iter_content(chunk_size=BUFFER_SIZE):
                    if not chunk:
                        continue
                    offset = 0
                    while offset < len(chunk):
                        remaining = PART_SIZE - current_size
                        piece = chunk[offset : offset + remaining]
                        current.write(piece)
                        full_hash.update(piece)
                        current_size += len(piece)
                        total += len(piece)
                        offset += len(piece)

                        if current_size == PART_SIZE:
                            current.close()
                            upload(tag, current_path)
                            parts.append(
                                {"name": current_name, "size": current_size}
                            )
                            current_path.unlink(missing_ok=True)

                            part_no += 1
                            current_name = asset_name(path, part_no)
                            current_path = tmpdir / current_name
                            current = current_path.open("wb")
                            current_size = 0
            finally:
                if not current.closed:
                    current.close()

            if current_size:
                upload(tag, current_path)
                parts.append({"name": current_name, "size": current_size})
                current_path.unlink(missing_ok=True)

    actual_sha256 = full_hash.hexdigest()
    if expected_size is not None and total != expected_size:
        raise RuntimeError(
            f"Size mismatch for {path}: expected {expected_size}, got {total}"
        )
    if expected_sha256 and actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"SHA-256 mismatch for {path}: expected {expected_sha256}, "
            f"got {actual_sha256}"
        )

    return {
        "path": path,
        "size": total,
        "sha256": actual_sha256,
        "upstream_sha256": expected_sha256,
        "parts": parts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--tag-prefix", default="upstream")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start < 0 or args.end < args.start:
        raise SystemExit("Invalid start/end range")

    api = HfApi()
    info = api.model_info(MODEL_ID, files_metadata=True)
    revision = info.sha
    if not revision:
        raise SystemExit("Upstream revision SHA is unavailable")

    siblings = sorted(info.siblings or [], key=lambda item: item.rfilename)
    if args.end >= len(siblings):
        raise SystemExit(
            f"--end {args.end} is outside the available range 0..{len(siblings)-1}"
        )

    tag = f"{args.tag_prefix}-{revision[:12]}"
    ensure_release(tag, revision)
    ensure_upstream_license(tag, revision)

    entries: list[dict[str, Any]] = []
    for index in range(args.start, args.end + 1):
        sibling = siblings[index]
        path = sibling.rfilename

        if path == "LICENSE":
            print(
                f"[{index}/{len(siblings)-1}] LICENSE already uploaded",
                flush=True,
            )
            continue

        print(f"[{index}/{len(siblings)-1}] mirroring {path}", flush=True)
        entries.append(
            stream_one(
                path=path,
                revision=revision,
                tag=tag,
                expected_size=getattr(sibling, "size", None),
                expected_sha256=get_sha256(sibling),
            )
        )

    manifest = {
        "model_id": MODEL_ID,
        "revision": revision,
        "range": {"start": args.start, "end": args.end},
        "part_size": PART_SIZE,
        "files": entries,
    }

    manifest_name = (
        f"manifest-{args.start:04d}-{args.end:04d}-{revision[:12]}.json"
    )
    manifest_path = Path(manifest_name)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    upload(tag, manifest_path)
    print(f"Uploaded manifest to release {tag}: {manifest_path.name}")


if __name__ == "__main__":
    main()
