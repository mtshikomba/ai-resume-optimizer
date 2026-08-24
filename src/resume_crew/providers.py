"""
Provider abstraction helpers for hosted LLM providers (OpenAI, Hugging Face, ...)
This module provides simple wiring: mapping friendly model names to provider-specific ids
and configuring environment variables (API keys) so downstream LLM clients use them.

This is intentionally lightweight: it sets env vars and returns resolved model ids.
"""
from typing import Optional
import os

# Friendly default mapping — adjust as needed
MODEL_ALIAS_MAP = {
    # project-friendly alias -> provider-specific model id
    "free-optimal": {
        "openai": "gpt-3.5-turbo",
        "huggingface": "mistral-7b-instruct",
    }
}


def resolve_model(provider: Optional[str], model_alias_or_id: Optional[str]) -> Optional[str]:
    """Resolve a model identifier for the given provider.

    If model_alias_or_id is a known alias (like "free-optimal"), map it to a provider id.
    Otherwise return model_alias_or_id unchanged.
    """
    if not model_alias_or_id:
        return None
    if model_alias_or_id in MODEL_ALIAS_MAP:
        if provider and provider.lower() in MODEL_ALIAS_MAP[model_alias_or_id]:
            return MODEL_ALIAS_MAP[model_alias_or_id][provider.lower()]
        # if provider not specified, pick the first available mapping
        return next(iter(MODEL_ALIAS_MAP[model_alias_or_id].values()))
    return model_alias_or_id


def configure_provider_env(provider: Optional[str], model: Optional[str], api_key: Optional[str]) -> dict:
    """Configure environment variables for the chosen provider.

    Returns a dict of environment variables that were set (for callers to merge into subprocess envs if desired).
    """
    set_env = {}
    if not provider:
        return set_env
    p = provider.lower()
    if p == "openai":
        if api_key:
            os.environ.setdefault("OPENAI_API_KEY", api_key)
            set_env["OPENAI_API_KEY"] = api_key
        # set a runtime model variable so other parts of the app can see it
        if model:
            os.environ.setdefault("RESUME_CREW_MODEL", model)
            set_env["RESUME_CREW_MODEL"] = model
    elif p == "huggingface":
        if api_key:
            os.environ.setdefault("HUGGINGFACE_API_KEY", api_key)
            set_env["HUGGINGFACE_API_KEY"] = api_key
        if model:
            os.environ.setdefault("RESUME_CREW_MODEL", model)
            set_env["RESUME_CREW_MODEL"] = model
    else:
        # Generic provider handling: set RESUME_CREW_PROVIDER and RESUME_CREW_MODEL
        os.environ.setdefault("RESUME_CREW_PROVIDER", provider)
        set_env["RESUME_CREW_PROVIDER"] = provider
        if api_key:
            # store an opaque key var name for custom providers
            key_name = f"{provider.upper()}_API_KEY"
            os.environ.setdefault(key_name, api_key)
            set_env[key_name] = api_key
        if model:
            os.environ.setdefault("RESUME_CREW_MODEL", model)
            set_env["RESUME_CREW_MODEL"] = model
    return set_env
