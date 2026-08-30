"""Configuration module for T10 Flight Option Finder.

Loads environment variables safely and prevents credential leakage in logs.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment from .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


class Config:
    """Application configuration with secret masking and validation."""

    def __init__(self):
        self.aviationstack_api_key = os.getenv("AVIATIONSTACK_API_KEY", "").strip()
        self.ignav_api_key = os.getenv("IGNAV_API_KEY", "").strip()
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.nvidia_base_url = os.getenv(
            "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ).strip()
        self.nvidia_model = os.getenv(
            "NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"
        ).strip()
        self.ignav_base_url = os.getenv(
            "IGNAV_BASE_URL", "https://ignav.com/api"
        ).strip()
        self.aviationstack_base_url = os.getenv(
            "AVIATIONSTACK_BASE_URL", "http://api.aviationstack.com/v1"
        ).strip()

    def validate(self, check_aviationstack: bool = True, check_ignav: bool = True, check_nvidia: bool = True) -> list[str]:
        """Validate presence of required configuration variables.
        
        Returns a list of missing configuration names (or empty list if valid).
        """
        missing = []
        if check_aviationstack and not self.aviationstack_api_key:
            missing.append("AVIATIONSTACK_API_KEY")
        if check_ignav and not self.ignav_api_key:
            missing.append("IGNAV_API_KEY")
        if check_nvidia and not self.nvidia_api_key:
            missing.append("NVIDIA_API_KEY")
        return missing

    def is_valid(self) -> bool:
        """Check if all essential keys are present."""
        return len(self.validate()) == 0

    @staticmethod
    def _mask_secret(secret: str) -> str:
        """Mask a sensitive secret value."""
        if not secret:
            return "<MISSING>"
        if len(secret) <= 8:
            return "***"
        return f"{secret[:4]}...{secret[-4:]}"

    def __repr__(self) -> str:
        return (
            f"Config("
            f"aviationstack_api_key={self._mask_secret(self.aviationstack_api_key)}, "
            f"ignav_api_key={self._mask_secret(self.ignav_api_key)}, "
            f"nvidia_api_key={self._mask_secret(self.nvidia_api_key)}, "
            f"nvidia_base_url='{self.nvidia_base_url}', "
            f"nvidia_model='{self.nvidia_model}', "
            f"ignav_base_url='{self.ignav_base_url}', "
            f"aviationstack_base_url='{self.aviationstack_base_url}'"
            f")"
        )

    def __str__(self) -> str:
        return self.__repr__()


# Singleton instance
config = Config()
