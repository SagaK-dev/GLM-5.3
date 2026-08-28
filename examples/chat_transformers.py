#!/usr/bin/env python3
from __future__ import annotations

from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "zai-org/GLM-5.3"


def main() -> None:
    print(
        "Loading GLM-5.3. If the checkpoint is not cached, this can trigger "
        "a very large download."
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype="auto",
    )

    messages = [{"role": "user", "content": "Who are you?"}]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=128)
    generated = outputs[0][inputs["input_ids"].shape[-1] :]
    print(tokenizer.decode(generated, skip_special_tokens=True))


if __name__ == "__main__":
    main()
