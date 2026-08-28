# Full GLM-5.3 mirror on GitHub

The official GLM-5.3 checkpoint cannot be stored unchanged in a normal GitHub repository.

## Why

GitHub blocks ordinary Git objects above 100 MiB. Git LFS has a per-file ceiling that is lower than many official GLM-5.3 weight shards. The official checkpoint contains 141 safetensors shards, many around 5.36 GB each.

This repository therefore uses **GitHub Releases** for any full GitHub-hosted mirror.

Large upstream files are split into chunks smaller than 1.9 GB. A manifest records the original path, size, upstream digest when available, and the ordered release assets needed to reconstruct the file.

## License compliance

The mirror tooling includes the upstream `LICENSE` file as an asset and preserves upstream filenames and provenance in the manifest.

GLM-5.3 is © 2026 Z.AI and is distributed under the custom GLM-5.3 License. The license permits copying and distribution, subject to its conditions. Always review the canonical current license before creating or redistributing a mirror:

https://huggingface.co/zai-org/GLM-5.3/blob/main/LICENSE

## Important cost / quota note

A complete mirror is hundreds of gigabytes. Do not run a full mirror without checking GitHub account limits, budgets, Actions concurrency, and any applicable acceptable-use restrictions.

The workflow is intentionally manual and range-based. It does not automatically start transferring the full checkpoint.

## Manual workflow

Open **Actions → Mirror upstream to Release → Run workflow** and select a file-index range.

The workflow:

1. resolves the current upstream revision;
2. creates or reuses a GitHub Release tied to that revision;
3. streams selected official files from `zai-org/GLM-5.3`;
4. splits large files into sub-1.9-GB assets;
5. uploads the parts;
6. uploads a JSON manifest;
7. includes the upstream LICENSE when its index is selected.

To reconstruct an uploaded file, use:

```bash
python scripts/restore_release_file.py \
  --manifest manifest.json \
  --file model-00001-of-00141.safetensors \
  --asset-dir ./downloaded-assets \
  --output-dir ./models/GLM-5.3
```

The reconstruction tool verifies the reconstructed SHA-256 when the manifest contains one.
