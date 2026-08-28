#!/usr/bin/env python3
from __future__ import annotations

from huggingface_hub import HfApi

MODEL_ID = "zai-org/GLM-5.3"


def human_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


def main() -> None:
    api = HfApi()
    info = api.model_info(MODEL_ID, files_metadata=True)

    sizes = [
        sibling.size
        for sibling in (info.siblings or [])
        if getattr(sibling, "size", None) is not None
    ]
    total = sum(sizes)

    print(f"Model: {MODEL_ID}")
    print(f"Revision SHA: {info.sha}")
    print(f"Private: {info.private}")
    print(f"Gated: {getattr(info, 'gated', None)}")
    print(f"Files: {len(info.siblings or [])}")
    if total:
        print(f"Reported repository size: {human_bytes(total)}")
    else:
        print("Reported repository size: unavailable")
    print("Canonical URL: https://huggingface.co/zai-org/GLM-5.3")


if __name__ == "__main__":
    main()
