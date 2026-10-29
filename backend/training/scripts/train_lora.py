"""
LoRA / QLoRA fine-tuning script.

Usage:
    python training/scripts/train_lora.py [--qlora] [--model MODEL_ID]

Requirements (install separately):
    pip install peft trl
    pip install bitsandbytes  # Linux/GPU only for QLoRA

Hardware:
    - LoRA on CPU: very slow, use only for testing with tiny models
    - LoRA on GPU (CUDA): recommended
    - QLoRA (4-bit): requires CUDA GPU + bitsandbytes

NOTE: Fine-tuning changes model behavior on the training distribution.
It does NOT add uploaded documents to the model's knowledge.
Use RAG for document-grounded answers.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import get_settings

settings = get_settings()


def load_dataset(path: str):
    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def validate_dataset(examples):
    for i, ex in enumerate(examples):
        assert "instruction" in ex, f"Example {i} missing 'instruction'"
        assert "response" in ex, f"Example {i} missing 'response'"
        assert isinstance(ex["instruction"], str) and ex["instruction"].strip()
        assert isinstance(ex["response"], str) and ex["response"].strip()
    print(f"Dataset validated: {len(examples)} examples.")


def format_prompt(instruction: str, response: str) -> str:
    return f"### Instruction:\n{instruction}\n\n### Response:\n{response}"


def train(model_id: str, dataset_path: str, output_dir: str, use_qlora: bool = False):
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
        from peft import LoraConfig, get_peft_model, TaskType
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install peft trl transformers accelerate")
        sys.exit(1)

    import torch

    examples = load_dataset(dataset_path)
    validate_dataset(examples)

    print(f"Loading base model: {model_id}")

    load_kwargs = {"trust_remote_code": True}

    if use_qlora:
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
            load_kwargs["quantization_config"] = bnb_config
            load_kwargs["device_map"] = "auto"
            print("QLoRA (4-bit) mode enabled.")
        except ImportError:
            print("bitsandbytes not available. Falling back to standard LoRA.")
            use_qlora = False

    if not use_qlora:
        load_kwargs["torch_dtype"] = torch.float32

    tokenizer = AutoTokenizer.from_pretrained(model_id, **{"trust_remote_code": True})
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)

    # LoRA config - target modules vary by architecture
    # facebook/opt-* uses: q_proj, v_proj
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        bias="none",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Tokenize dataset
    texts = [format_prompt(ex["instruction"], ex["response"]) for ex in examples]
    encodings = tokenizer(
        texts,
        truncation=True,
        max_length=256,
        padding="max_length",
        return_tensors="pt",
    )

    import torch
    from torch.utils.data import Dataset, DataLoader

    class SimpleDataset(Dataset):
        def __init__(self, encodings):
            self.input_ids = encodings["input_ids"]
            self.attention_mask = encodings["attention_mask"]

        def __len__(self):
            return len(self.input_ids)

        def __getitem__(self, idx):
            return {
                "input_ids": self.input_ids[idx],
                "attention_mask": self.attention_mask[idx],
                "labels": self.input_ids[idx].clone(),
            }

    dataset = SimpleDataset(encodings)
    loader = DataLoader(dataset, batch_size=2, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)
    model.train()

    os.makedirs(output_dir, exist_ok=True)
    num_epochs = 3
    print(f"Training for {num_epochs} epochs...")

    for epoch in range(num_epochs):
        total_loss = 0
        for batch in loader:
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch + 1}/{num_epochs} - Loss: {avg_loss:.4f}")

    # Save adapter
    adapter_path = os.path.join(output_dir, "lora_adapter")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"LoRA adapter saved to: {adapter_path}")

    return adapter_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoRA/QLoRA fine-tuning")
    parser.add_argument("--model", default=settings.finetune_base_model)
    parser.add_argument("--dataset", default=settings.finetune_dataset)
    parser.add_argument("--output", default=settings.finetune_output_dir)
    parser.add_argument("--qlora", action="store_true", help="Use QLoRA (requires GPU + bitsandbytes)")
    args = parser.parse_args()

    adapter_path = train(args.model, args.dataset, args.output, use_qlora=args.qlora)
    print(f"\nTraining complete. Adapter at: {adapter_path}")
    print("Run evaluation with: python training/evaluation/evaluate.py --adapter", adapter_path)
