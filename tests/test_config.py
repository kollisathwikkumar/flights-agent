"""Unit tests for configuration loading, validation, and secret masking."""

import os
import pytest
from config import Config


def test_config_loads_from_env(monkeypatch):
    """Test that Config loads environment variables correctly."""
    monkeypatch.setenv("AVIATIONSTACK_API_KEY", "test_aviation_key_12345")
    monkeypatch.setenv("IGNAV_API_KEY", "test_ignav_key_67890")
    monkeypatch.setenv("NVIDIA_API_KEY", "test_nvidia_key_abcde")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://test.api.nvidia.com/v1")
    monkeypatch.setenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

    cfg = Config()
    assert cfg.aviationstack_api_key == "test_aviation_key_12345"
    assert cfg.ignav_api_key == "test_ignav_key_67890"
    assert cfg.nvidia_api_key == "test_nvidia_key_abcde"
    assert cfg.nvidia_base_url == "https://test.api.nvidia.com/v1"
    assert cfg.nvidia_model == "meta/llama-3.3-70b-instruct"
    assert cfg.is_valid() is True
    assert cfg.validate() == []


def test_config_detects_missing_keys(monkeypatch):
    """Test that Config detects missing API keys."""
    monkeypatch.setenv("AVIATIONSTACK_API_KEY", "")
    monkeypatch.setenv("IGNAV_API_KEY", "")
    monkeypatch.setenv("NVIDIA_API_KEY", "")

    cfg = Config()
    missing = cfg.validate()
    assert "AVIATIONSTACK_API_KEY" in missing
    assert "IGNAV_API_KEY" in missing
    assert "NVIDIA_API_KEY" in missing
    assert cfg.is_valid() is False


def test_config_masks_secrets_in_repr(monkeypatch):
    """Test that API keys are never printed in full in repr or str."""
    secret = "secret_key_1234567890_very_long"
    monkeypatch.setenv("AVIATIONSTACK_API_KEY", secret)
    monkeypatch.setenv("IGNAV_API_KEY", secret)
    monkeypatch.setenv("NVIDIA_API_KEY", secret)

    cfg = Config()
    repr_str = repr(cfg)
    str_str = str(cfg)

    # The full secret must NEVER appear
    assert secret not in repr_str
    assert secret not in str_str
    # The masked version should appear
    assert "secr...long" in repr_str
