# Official GLM-5.3 Open-Source Mirror Scope

This repository mirrors the unique official Z.AI / zai-org GLM-5.3-family open-source and open-weight distributions that are publicly released as of 2026-08-29.

## Canonical official artifacts

### 1. zai-org/GLM-5.3

- Type: FP8 open-weight model repository
- Canonical upstream: https://huggingface.co/zai-org/GLM-5.3
- License: GLM-5.3 License
- Mirror state: complete
- Verified upstream revision: `935644c05e76fc198714f4cca449fd8b970ff6d7`
- All 141 model shards and all other upstream files are mirrored in GitHub Releases.
- Completion record: `MIRROR_STATUS.json`

### 2. zai-org/GLM-5.3-BF16

- Type: BF16 open-weight model repository
- Canonical upstream: https://huggingface.co/zai-org/GLM-5.3-BF16
- License: GLM-5.3 License
- Mirror layout: four segmented GitHub Releases
- Completion record: `official-models/GLM-5.3-BF16/MIRROR_STATUS.json`

### 3. zai-org/GLM-5.3-Flash

- Type: FP8 / mixed-tensor open-weight model repository
- Canonical upstream: https://huggingface.co/zai-org/GLM-5.3-Flash
- License: MIT
- Mirror state: complete
- Verified upstream revision: `04c4e9e95c5da8862dced7e5056455116f83a7e0`
- Verified upstream files: 72 / 72
- Verified bytes: 328366172315
- Mirror layout: four segmented GitHub Releases
- Completion record: `official-models/GLM-5.3-Flash/MIRROR_STATUS.json`

### 4. zai-org/GLM-5.3-Flash-BF16

- Type: BF16 open-weight model repository
- Canonical upstream: https://huggingface.co/zai-org/GLM-5.3-Flash-BF16
- License: MIT
- Mirror state: complete
- Verified upstream revision: `f12e0fe1f6b2ea274c11a569582edfd99d993c5e`
- Verified upstream files: 130 / 130
- Verified bytes: 642676400602
- Mirror layout: four segmented GitHub Releases
- Completion record: `official-models/GLM-5.3-Flash-BF16/MIRROR_STATUS.json`

### 5. zai-org/GLM-5

- Type: official GitHub source/documentation repository for GLM-5.3, GLM-5.2, GLM-5.1 and GLM-5
- Canonical upstream: https://github.com/zai-org/GLM-5
- License: Apache-2.0
- Pinned upstream commit: `414ad9eb891b05b5d7d51d573939bfe9ce538223`
- Mirror location: `official-source/zai-org-GLM-5/`
- The 22 upstream files are copied byte-for-byte and verified before commit.

## What is intentionally not duplicated

The official GLM-5 repository links to third-party or separately maintained inference and training projects such as vLLM, SGLang, Transformers, KTransformers, Unsloth and ms-swift. Those projects are not the Z.AI GLM-5.3 distribution itself and are therefore not vendored into this repository.

ModelScope is an additional official download endpoint for the same named model releases. The canonical unique model artifacts are mirrored from zai-org on Hugging Face; duplicate hosting endpoints are not separately copied as another set of identical weights.

## License preservation

Every model Release includes the upstream model LICENSE. The vendored official GitHub source includes its upstream Apache-2.0 LICENSE unchanged.

This repository does not replace or relicense upstream rights. Z.AI and the relevant upstream rights holders retain their copyright and license terms.

## Verification policy

A model variant is considered complete only when its generated `MIRROR_STATUS.json` reports:

- `status: complete`
- all upstream paths present
- all Release part sizes matching manifests
- upstream SHA-256 checked where available
- upstream LICENSE present
- pinned upstream metadata present
