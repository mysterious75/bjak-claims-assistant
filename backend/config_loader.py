"""Configuration loader - reads config.yaml"""

import os
import yaml
from typing import Any, Dict


_config_cache: Dict[str, Any] = None


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    config_path = os.path.abspath(config_path)
    
    if not os.path.exists(config_path):
        _config_cache = _get_defaults()
        return _config_cache
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}
    
    # Merge with defaults
    defaults = _get_defaults()
    _config_cache = _deep_merge(defaults, config)
    
    return _config_cache


def _get_defaults() -> Dict[str, Any]:
    """Return default configuration."""
    return {
        "llm": {
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "fallback_model": "gemini-2.5-flash-lite",
            "temperature": 0.3,
            "max_tokens": 2048,
        },
        "rag": {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "top_k": 5,
            "vectorstore_path": "./vectorstore",
        },
        "claims": {
            "statuses": ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"],
            "claim_types": ["health", "motor", "life", "travel"],
        },
        "app": {
            "title": "BJAK AI Claims Assistant",
            "version": "1.0.0",
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_config() -> Dict[str, Any]:
    """Get cached configuration."""
    return load_config()


def reload_config():
    """Force reload configuration."""
    global _config_cache
    _config_cache = None
    return load_config()
