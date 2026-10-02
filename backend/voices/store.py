from __future__ import annotations
from datetime import datetime, timezone
import json, os, re
from pathlib import Path
from typing import Any
from ..config import app_data_dir
from ..security.audit import (
    DEFAULT_VOICE_CONSENT_STATEMENT,
    file_sha256,
    now_iso,
    record_consent_event,
)

VOICE_ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')

class InvalidVoiceId(ValueError):
    pass

BUILTIN_VOICES = [
    {
        "id": "vi-standard",
        "name": "Giọng Tiếng Việt chuẩn",
        "language": "vi",
        "isClone": False,
        "isBuiltin": True,
        "description": "Giọng đọc tiếng Việt tự nhiên mặc định của VoxCPM2",
        "referenceAudio": None,
        "referenceAudioSha256": None,
        "referenceText": "",
        "consentConfirmed": True,
        "consentTimestamp": None,
        "consentStatement": None,
    },
    {
        "id": "en-standard",
        "name": "Standard English Voice",
        "language": "en",
        "isClone": False,
        "isBuiltin": True,
        "description": "VoxCPM2 default natural English narration voice",
        "referenceAudio": None,
        "referenceAudioSha256": None,
        "referenceText": "",
        "consentConfirmed": True,
        "consentTimestamp": None,
        "consentStatement": None,
    },
]

class VoiceProfileStore:
    def __init__(self, root: Path | None = None):
        self.root = root or app_data_dir() / "voices"
        self.root.mkdir(parents=True, exist_ok=True)

    def _validate_id(self, voice_id: str) -> str:
        voice_id = voice_id.strip().lower()
        if not VOICE_ID_RE.fullmatch(voice_id):
            raise InvalidVoiceId(f"Voice ID không hợp lệ: '{voice_id}'. Chỉ dùng chữ thường, số và dấu gạch nối (1-64 ký tự).")
        return voice_id

    def path(self, voice_id: str) -> Path:
        return self.root / f"{self._validate_id(voice_id)}.json"

    def list(self) -> list[dict]:
        custom_voices = []
        for file in self.root.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                custom_voices.append(data)
            except (OSError, json.JSONDecodeError):
                continue
        custom_voices.sort(key=lambda x: x.get("updatedAt", x.get("createdAt", "")), reverse=True)
        return list(BUILTIN_VOICES) + custom_voices

    def get(self, voice_id: str) -> dict:
        voice_id = voice_id.strip().lower()
        for b in BUILTIN_VOICES:
            if b["id"] == voice_id:
                return dict(b)
        path = self.path(voice_id)
        if not path.is_file():
            raise KeyError(f"Voice profile không tồn tại: {voice_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def create(
        self,
        voice_id: str,
        name: str,
        language: str = "vi",
        is_clone: bool = False,
        reference_audio: Path | str | None = None,
        reference_text: str = "",
        consent_confirmed: bool = False,
        consent_statement: str = DEFAULT_VOICE_CONSENT_STATEMENT,
    ) -> dict:
        vid = self._validate_id(voice_id)
        if any(b["id"] == vid for b in BUILTIN_VOICES):
            raise ValueError(f"Không thể ghi đè voice mặc định: {vid}")

        ref_path: Path | None = Path(reference_audio) if reference_audio else None
        audio_sha256 = None

        if is_clone:
            if not ref_path:
                raise ValueError("Voice clone yêu cầu đường dẫn reference audio")
            if not ref_path.is_file():
                raise FileNotFoundError(f"Không tìm thấy file reference audio: {ref_path}")
            if not consent_confirmed:
                raise PermissionError("Voice clone yêu cầu người dùng xác nhận quyền sử dụng giọng mẫu và cam kết pháp lý")
            audio_sha256 = file_sha256(ref_path)
            # Ghi lại sự kiện audit consent
            record_consent_event(
                voice_id=vid,
                name=name,
                reference_audio=ref_path,
                reference_text=reference_text,
                statement=consent_statement or DEFAULT_VOICE_CONSENT_STATEMENT,
                root=self.root.parent,
            )

        now = now_iso()
        data = {
            "id": vid,
            "name": name.strip() or vid,
            "language": language,
            "isClone": bool(is_clone),
            "isBuiltin": False,
            "referenceAudio": str(ref_path.resolve()) if ref_path else None,
            "referenceAudioSha256": audio_sha256,
            "referenceText": reference_text.strip(),
            "consentConfirmed": bool(consent_confirmed) if is_clone else True,
            "consentTimestamp": now if is_clone else None,
            "consentStatement": (consent_statement or DEFAULT_VOICE_CONSENT_STATEMENT) if is_clone else None,
            "createdAt": now,
            "updatedAt": now,
        }

        target = self.path(vid)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, target)
        return data

    def delete(self, voice_id: str) -> bool:
        vid = self._validate_id(voice_id)
        if any(b["id"] == vid for b in BUILTIN_VOICES):
            raise ValueError(f"Không thể xóa giọng mặc định: {vid}")
        target = self.path(vid)
        if not target.is_file():
            raise KeyError(f"Voice profile không tồn tại: {vid}")
        target.unlink()
        return True
