#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests
from huggingface_hub import HfApi, hf_hub_url
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

MODEL_ID = "zai-org/GLM-5.3"
PART_SIZE = 1_900_000_000
BUFFER_SIZE = 8 * 1024 * 1024


def run_with_retry(*args: str, attempts: int = 6) -> None:
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(1, attempts + 1):
        try:
            subprocess.run(args, check=True)
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc
            if attempt == attempts:
                raise
            delay = min(60, 2 ** attempt)
            print(
                f"Command failed (attempt {attempt}/{attempts}); "
                f"retrying in {delay}s: {' '.join(args[:4])}",
                flush=True,
            )
            time.sleep(delay)
    if last_error is not None:
        raise last_error


def build_session() -> requests.Session:
    retry = Retry(
        total=8,
        connect=8,
        read=3,
        status=8,
        backoff_factor=2.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


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
    run_with_retry("gh", "release", "upload", tag, str(path), "--clobber")


def ensure_release(tag: str, revision: str) -> None:
    result = subprocess.run(
        ["gh", "release", "view", tag],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return
    run_with_retry(
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
    session = build_session()
    with session.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with tempfile.TemporaryDirectory(prefix="glm53-license-") as tmp:
            path = Path(tmp) / "LICENSE"
            with path.open("wb") as out:
                for chunk in response.iter_content(chunk_size=BUFFER_SIZE):
                    if chunk:
                        out.write(chunk)
            upload(tag, path)


def manifest_name(start: int, end: int, revision: str) -> str:
    return f"manifest-{start:04d}-{end:04d}-{revision[:12]}.json"


def manifest_exists(tag: str, name: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="glm53-manifest-check-") as tmp:
        result = subprocess.run(
            [
                "gh",
                "release",
                "download",
                tag,
                "--pattern",
                name,
                "--dir",
                tmp,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0 and (Path(tmp) / name).is_file()


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
    session = build_session()

    with session.get(url, stream=True, timeout=(30, 300)) as response:
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
    parser.add_argument(
        "--revision",
        default=None,
        help="Pin an exact upstream revision SHA. Defaults to current upstream.",
    )
    parser.add_argument(
        "--skip-license",
        action="store_true",
        help="Do not upload LICENSE; useful when a prepare job already did it.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Directly mirror one pinned upstream path without querying model_info.",
    )
    parser.add_argument("--expected-size", type=int, default=None)
    parser.add_argument("--expected-sha256", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start < 0 or args.end < args.start:
        raise SystemExit("Invalid start/end range")

    if args.path:
        if not args.revision:
            raise SystemExit("--revision is required when --path is used")
        revision = args.revision
        tag = f"{args.tag_prefix}-{revision[:12]}"
        ensure_release(tag, revision)
        if not args.skip_license:
            ensure_upstream_license(tag, revision)

        name = manifest_name(args.start, args.end, revision)
        if manifest_exists(tag, name):
            print(
                f"Already complete, skipping {args.path}; found {name}",
                flush=True,
            )
            return

        if args.path == "LICENSE":
            print("LICENSE is handled separately", flush=True)
            return

        entry = stream_one(
            path=args.path,
            revision=revision,
            tag=tag,
            expected_size=args.expected_size,
            expected_sha256=args.expected_sha256 or None,
        )
        manifest = {
            "model_id": MODEL_ID,
            "revision": revision,
            "range": {"start": args.start, "end": args.end},
            "part_size": PART_SIZE,
            "files": [entry],
        }
        manifest_path = Path(name)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        upload(tag, manifest_path)
        print(f"Uploaded manifest to release {tag}: {name}")
        return

    api = HfApi()
    info = api.model_info(
        MODEL_ID,
        revision=args.revision,
        files_metadata=True,
    )
    revision = info.sha
    if not revision:
        raise SystemExit("Upstream revision SHA is unavailable")

    if args.revision and revision != args.revision:
        raise SystemExit(
            f"Resolved revision mismatch: requested {args.revision}, got {revision}"
        )

    siblings = sorted(info.siblings or [], key=lambda item: item.rfilename)
    if args.end >= len(siblings):
        raise SystemExit(
            f"--end {args.end} is outside the available range 0..{len(siblings)-1}"
        )

    tag = f"{args.tag_prefix}-{revision[:12]}"
    ensure_release(tag, revision)
    if not args.skip_license:
        ensure_upstream_license(tag, revision)

    name = manifest_name(args.start, args.end, revision)
    if manifest_exists(tag, name):
        print(f"Already complete, skipping range; found {name}", flush=True)
        return

    entries: list[dict[str, Any]] = []
    for index in range(args.start, args.end + 1):
        sibling = siblings[index]
        path = sibling.rfilename

        if path == "LICENSE":
            print(
                f"[{index}/{len(siblings)-1}] LICENSE handled separately",
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

    manifest_path = Path(name)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    upload(tag, manifest_path)
    print(f"Uploaded manifest to release {tag}: {manifest_path.name}")


if __name__ == "__main__":
    main()
