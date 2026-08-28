# GLM-5.3

This repository provides a reproducible launcher and GitHub-mirroring toolchain for the official **Z.ai GLM-5.3** open-weights model.

## Official upstream

- Model: `zai-org/GLM-5.3`
- Upstream host: Hugging Face
- Publisher: Z.ai
- Approximate upstream size: ~756 GB
- Weight layout: 141 safetensors shards, many around 5.36 GB each
- License: custom `GLM-5.3 License`

## Important GitHub storage limitation

The official weight files cannot be committed unchanged to an ordinary GitHub repository:

- ordinary GitHub repositories reject files above 100 MiB;
- Git LFS has per-file limits below the size of many official GLM-5.3 weight shards.

For a complete GitHub-hosted mirror, this repository therefore uses **GitHub Releases**. Large upstream files are split into chunks smaller than 1.9 GB and can later be reconstructed byte-for-byte.

See [MIRRORING.md](MIRRORING.md).

The mirroring workflow is intentionally manual because a complete copy is hundreds of gigabytes and can have account, quota, Actions, and billing implications.

## License / redistribution

GLM-5.3 is © 2026 Z.AI and is distributed under the custom GLM-5.3 License.

The license permits use, copying, modification, publication, distribution, sublicensing, selling copies, deployment, fine-tuning, and creation of derivative works, subject to its stated conditions.

For redistribution, the Z.AI copyright notice and permission notice must be preserved. The mirror tooling therefore uploads the canonical upstream `LICENSE` file to every GitHub Release it creates.

The license also contains a special condition for very large Model-as-a-Service businesses: if the licensee or affiliates operate such a business and their aggregate revenue exceeds the stated threshold over a consecutive 12-month period, Z.AI security review is required before commercial use.

Always review the current canonical license before redistribution:

https://huggingface.co/zai-org/GLM-5.3/blob/main/LICENSE

## Quick start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

### 2. Install dependencies

For direct Transformers use:

```bash
pip install -r requirements-transformers.txt
```

For vLLM serving:

```bash
pip install vllm
```

For SGLang serving:

```bash
pip install sglang
```

### 3. Check upstream metadata without downloading weights

```bash
python scripts/check_upstream.py
```

### 4. Download the model locally

```bash
python scripts/download_model.py --local-dir ./models/GLM-5.3 --confirm-large-download
```

### 5. Serve with vLLM

```bash
bash scripts/serve_vllm.sh
```

### 6. Serve with SGLang

```bash
bash scripts/serve_sglang.sh
```

## Direct Transformers example

```bash
python examples/chat_transformers.py
```

This may download the full checkpoint if it is not already cached.

## Full GitHub mirror tooling

The repository now contains:

- `.github/workflows/mirror-release.yml` — manual range-based mirror workflow;
- `scripts/mirror_release_assets.py` — streams official upstream files and uploads split GitHub Release assets;
- `scripts/restore_release_file.py` — reconstructs the original files and verifies SHA-256;
- `MIRRORING.md` — operational and licensing notes.

## Repository policy

This repository does not claim authorship of GLM-5.3. Model weights, architecture assets, upstream configuration, and upstream license rights remain attributable to Z.AI and the relevant upstream rights holders.
