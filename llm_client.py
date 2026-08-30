"""NVIDIA NIM LLM Client for T10 Flight Option Finder.

Communicates with NVIDIA NIM /v1/chat/completions endpoint using standard function calling / tools.
Handles errors transparently without silent provider substitution or key leakage.
"""

import logging
from typing import Any, Optional
import requests

from config import config

logger = logging.getLogger(__name__)


class NIMError(Exception):
    """Exception raised for NVIDIA NIM API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class NIMClient:
    """Client for NVIDIA NIM LLM Chat Completions and Tool Calling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else config.nvidia_api_key
        self.base_url = (base_url or config.nvidia_base_url).rstrip("/")
        self.model = model or config.nvidia_model

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise NIMError("NVIDIA_API_KEY is not configured.")
        
        auth_token = self.api_key
        if not auth_token.startswith("Bearer "):
            auth_token = f"Bearer {auth_token}"

        return {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Send a chat completion request to NVIDIA NIM.
        
        Returns the parsed message dict containing 'content' and optional 'tool_calls'.
        """
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
        except (requests.Timeout, requests.ConnectionError) as e:
            raise NIMError(f"Network error connecting to NVIDIA NIM: {str(e)}") from e

        if response.status_code == 410:
            raise NIMError(
                f"NVIDIA NIM model '{self.model}' is deprecated or gone (HTTP 410): {response.text[:300]}",
                status_code=410,
                response_body=response.text,
            )

        if response.status_code in (401, 403):
            raise NIMError(
                f"NVIDIA NIM authorization failed (HTTP {response.status_code}): {response.text[:300]}",
                status_code=response.status_code,
                response_body=response.text,
            )

        if not response.ok:
            raise NIMError(
                f"NVIDIA NIM API error (HTTP {response.status_code}): {response.text[:300]}",
                status_code=response.status_code,
                response_body=response.text,
            )

        try:
            data = response.json()
        except ValueError as e:
            raise NIMError("NVIDIA NIM returned malformed JSON response.", response_body=response.text[:300]) from e

        choices = data.get("choices", [])
        if not choices:
            raise NIMError("NVIDIA NIM returned an empty choices list.", response_body=response.text[:300])

        message = choices[0].get("message", {})
        return message


# Singleton instance
nim_client = NIMClient()
