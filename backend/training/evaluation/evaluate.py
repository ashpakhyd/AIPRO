"""
Evaluation script: compare base model vs LoRA adapter responses.

Usage:
    python training/evaluation/evaluate.py --adapter ./training/output/lora_adapter
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import get_settings

settings = get_settings()

EVAL_EXAMPLES = [
    {"instruction": "What is machine learning?", "expected_keywords": ["data", "learn", "algorithm"]},
    {"instruction": "What is LoRA?", "expected_keywords": ["low-rank", "fine-tuning", "adapter"]},
    {"instruction": "What is a transformer model?", "expected_keywords": ["attention", "neural", "sequence"]},
]


def generate_response(model, tokenizer, instruction: str, max_new_tokens: int = 100) -> str:
    import torch
    prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "### Response:" in decoded:
        return decoded.split("### Response:")[-1].strip()
    return decoded.strip()


def score_response(response: str, keywords: list) -> float:
    response_lower = response.lower()
    hits = sum(1 for kw in keywords if kw.lower() in response_lower)
    return hits / len(keywords) if keywords else 0.0


def evaluate(model_id: str, adapter_path: str = None):
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    print(f"Loading base model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float32, trust_remote_code=True
    )
    base_model.eval()

    results = []
    print("\n--- Base Model Evaluation ---")
    for ex in EVAL_EXAMPLES:
        response = generate_response(base_model, tokenizer, ex["instruction"])
        score = score_response(response, ex["expected_keywords"])
        print(f"Q: {ex['instruction']}")
        print(f"A: {response[:200]}")
        print(f"Keyword score: {score:.2f}\n")
        results.append({"instruction": ex["instruction"], "base_score": score, "base_response": response})

    if adapter_path:
        print(f"\n--- LoRA Adapter Evaluation ({adapter_path}) ---")
        from peft import PeftModel
        lora_model = PeftModel.from_pretrained(base_model, adapter_path)
        lora_model.eval()

        for i, ex in enumerate(EVAL_EXAMPLES):
            response = generate_response(lora_model, tokenizer, ex["instruction"])
            score = score_response(response, ex["expected_keywords"])
            print(f"Q: {ex['instruction']}")
            print(f"A: {response[:200]}")
            print(f"Keyword score: {score:.2f}\n")
            results[i]["lora_score"] = score
            results[i]["lora_response"] = response

    # Summary
    print("\n--- Evaluation Summary ---")
    for r in results:
        base = r.get("base_score", 0)
        lora = r.get("lora_score", "N/A")
        improvement = f"+{lora - base:.2f}" if isinstance(lora, float) else "N/A"
        print(f"  {r['instruction'][:50]}: base={base:.2f}, lora={lora}, improvement={improvement}")

    report_path = Path(adapter_path).parent / "eval_report.json" if adapter_path else Path("eval_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=settings.finetune_base_model)
    parser.add_argument("--adapter", default=None, help="Path to saved LoRA adapter")
    args = parser.parse_args()
    evaluate(args.model, args.adapter)
