# GLM-5.3

This repository is a lightweight, reproducible launcher for the official **Z.ai GLM-5.3** open-weights model.

## Official upstream

- Model: `zai-org/GLM-5.3`
- Upstream host: Hugging Face
- Publisher: Z.ai
- Model size: about 756 GB on the upstream repository
- License: custom `GLM-5.3 License`

The model weights are **not vendored into this GitHub repository** because the upstream checkpoint is hundreds of gigabytes and is not suitable for ordinary GitHub storage. The scripts here pull the model directly from the official upstream source.

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

### 3. Check upstream metadata without downloading the weights

```bash
python scripts/check_upstream.py
```

### 4. Download the model only when you have enough storage

```bash
python scripts/download_model.py --local-dir ./models/GLM-5.3 --confirm-large-download
```

The script intentionally requires an explicit confirmation flag because the upstream repository is extremely large.

### 5. Serve with vLLM

```bash
bash scripts/serve_vllm.sh
```

Default endpoint:

```text
http://localhost:8000/v1/chat/completions
```

### 6. Serve with SGLang

```bash
bash scripts/serve_sglang.sh
```

Default endpoint:

```text
http://localhost:30000/v1/chat/completions
```

## Direct Transformers example

```bash
python examples/chat_transformers.py
```

This may download the full checkpoint if it is not already cached.

## Reasoning effort

GLM-5.3 supports `low`, `high`, and `max` reasoning effort. The official model card states that the default is `max`.

## Repository policy

This repository does not claim authorship of GLM-5.3. Model weights, architecture assets, upstream configuration, and the GLM-5.3 license belong to their respective upstream rights holders.

Do not replace the upstream model identifier with unofficial mirrors unless you have independently verified their provenance.

## License notice

GLM-5.3 is distributed by Z.ai under the custom GLM-5.3 License. Review the official license before redistribution, commercial deployment, or offering the model as a service.

This repository's helper scripts are provided for reproducible access to the official upstream model.