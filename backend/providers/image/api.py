from __future__ import annotations
import base64, json, os, urllib.request
from pathlib import Path
from .base import ImageRequest

class ApiImageProvider:
    """Generic JSON image API. Supports base64 payloads or returned download URLs."""
    def __init__(self, endpoint: str, model: str, api_key_env: str = "IMAGE_API_KEY"):
        self.endpoint, self.model, self.api_key_env = endpoint, model, api_key_env

    def generate(self, request: ImageRequest) -> Path:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError(f"Thiếu API key trong biến {self.api_key_env}")
        body = json.dumps({"model": self.model, "prompt": request.prompt,
                           "size": f"{request.width}x{request.height}", "n": 1}).encode()
        req = urllib.request.Request(self.endpoint, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as response:
            data = json.load(response)
        item = data["data"][0]
        if item.get("b64_json"):
            payload = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=300) as image_response:
                payload = image_response.read()
        else:
            raise RuntimeError("API không trả b64_json hoặc url")
        request.output.parent.mkdir(parents=True, exist_ok=True)
        request.output.write_bytes(payload)
        return request.output
