# Upstream provenance

This repository is wired to the official Z.ai model repository:

- Publisher: Z.ai
- Model ID: `zai-org/GLM-5.3`
- Canonical model page: https://huggingface.co/zai-org/GLM-5.3
- Canonical license page: https://huggingface.co/zai-org/GLM-5.3/blob/main/LICENSE

## Important

GLM-5.3 uses a custom license named **GLM-5.3 License**. It is not represented here as MIT, Apache-2.0, BSD, or another standard permissive license.

Before redistributing model files, operating a commercial service, or creating a derivative distribution, read the current upstream license directly from Z.ai's official repository.

## Weight storage

The upstream model repository is hundreds of gigabytes. GitHub is therefore used here for launcher code, documentation, and reproducible tooling rather than for vendoring the checkpoint.

The scripts always default to the canonical `zai-org/GLM-5.3` model ID.
