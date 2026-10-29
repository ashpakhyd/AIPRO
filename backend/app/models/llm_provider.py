"""
LLM provider abstraction.
Supports: huggingface_local | huggingface_api | openai_compatible
"""
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = _load_llm()
    return _llm


def _load_llm():
    provider = settings.llm_provider
    logger.info(f"Loading LLM provider: {provider}")

    if provider == "huggingface_local":
        return _load_hf_local()
    elif provider == "huggingface_api":
        return _load_hf_api()
    elif provider == "openai_compatible":
        return _load_openai_compatible()
    elif provider == "groq":
        return _load_groq()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Choose: huggingface_local, huggingface_api, openai_compatible"
        )


def _load_hf_local():
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch

    model_id = settings.llm_model_id
    logger.info(f"Loading local HF model: {model_id} (first run downloads the model)")

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        device_map=settings.llm_device,
        trust_remote_code=True,
    )
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=settings.llm_max_new_tokens,
        temperature=settings.llm_temperature,
        do_sample=settings.llm_temperature > 0,
        return_full_text=False,
    )

    # Wrap pipeline in a simple callable
    class PipelineLLM:
        def invoke(self, prompt: str) -> str:
            result = pipe(prompt)
            return result[0]["generated_text"]

    return PipelineLLM()


def _load_hf_api():
    if not settings.huggingface_api_key:
        raise ValueError("HUGGINGFACE_API_KEY is required for huggingface_api provider.")
    from huggingface_hub import InferenceClient

    client = InferenceClient(api_key=settings.huggingface_api_key)

    class HFInferenceLLM:
        def invoke(self, prompt: str) -> str:
            result = client.chat.completions.create(
                model=settings.hf_inference_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.llm_max_new_tokens,
                temperature=settings.llm_temperature,
            )
            return result.choices[0].message.content

    return HFInferenceLLM()


def _load_groq():
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is required for groq provider.")
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)

    class GroqLLM:
        def invoke(self, prompt: str) -> str:
            result = client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.llm_max_new_tokens,
                temperature=settings.llm_temperature,
            )
            return result.choices[0].message.content

    return GroqLLM()


def _load_openai_compatible():
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for openai_compatible provider.")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        max_tokens=settings.llm_max_new_tokens,
        temperature=settings.llm_temperature,
    )


def check_llm_ready() -> bool:
    try:
        get_llm()
        return True
    except Exception as e:
        logger.warning(f"LLM not ready: {e}")
        return False


def is_llm_local() -> bool:
    return settings.llm_provider == "huggingface_local"


def generate_text(prompt: str) -> str:
    llm = get_llm()
    try:
        result = llm.invoke(prompt)
        if hasattr(result, "content"):
            return result.content
        return str(result)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise
