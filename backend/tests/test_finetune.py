import pytest
import json
from pathlib import Path


DATASET_PATH = Path(__file__).parent.parent / "training" / "datasets" / "sample_dataset.jsonl"


def test_dataset_exists():
    assert DATASET_PATH.exists(), f"Dataset not found at {DATASET_PATH}"


def test_dataset_valid_jsonl():
    examples = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
                examples.append(ex)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON on line {i + 1}: {e}")
    assert len(examples) >= 5, "Dataset should have at least 5 examples"


def test_dataset_required_fields():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            assert "instruction" in ex, f"Line {i + 1} missing 'instruction'"
            assert "response" in ex, f"Line {i + 1} missing 'response'"
            assert ex["instruction"].strip(), f"Line {i + 1} has empty instruction"
            assert ex["response"].strip(), f"Line {i + 1} has empty response"


def test_dataset_no_sensitive_data():
    sensitive_patterns = ["api_key", "password", "secret", "sk-", "hf_"]
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        content = f.read().lower()
    for pattern in sensitive_patterns:
        assert pattern not in content, f"Dataset may contain sensitive data: '{pattern}'"
