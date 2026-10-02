from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json, os, uuid
from pathlib import Path
from ..config import app_data_dir

DEFAULT_VOICE_CONSENT_STATEMENT = (
    "Tôi cam kết rằng tôi sở hữu hoặc đã được chủ sở hữu ủy quyền hợp pháp bằng văn bản "
    "để sử dụng mẫu giọng nói này cho mục đích tổng hợp giọng nói AI (Voice Clone). "
    "Tôi cam kết không sử dụng giọng nói này để mạo danh, lừa đảo, tạo tin giả hoặc "
    "vi phạm pháp luật và quyền riêng tư của cá nhân khác."
)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def file_sha256(path: Path | None) -> str | None:
    if not path or not path.is_file():
        return None
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None

def audit_dir(root: Path | None = None) -> Path:
    target = (root or app_data_dir()) / "audit"
    target.mkdir(parents=True, exist_ok=True)
    return target

def audit_log_path(root: Path | None = None) -> Path:
    return audit_dir(root) / "voice_clones.jsonl"

def append_audit_record(record: dict, root: Path | None = None) -> None:
    log_file = audit_log_path(root)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)

def record_consent_event(
    voice_id: str,
    name: str,
    reference_audio: Path,
    reference_text: str = "",
    statement: str = DEFAULT_VOICE_CONSENT_STATEMENT,
    user: str = "local-user",
    root: Path | None = None
) -> dict:
    audio_hash = file_sha256(reference_audio)
    record = {
        "id": str(uuid.uuid4()),
        "event": "voice_clone_consent_granted",
        "timestamp": now_iso(),
        "voice_id": voice_id,
        "voice_name": name,
        "reference_audio": str(reference_audio.resolve()) if reference_audio.exists() else str(reference_audio),
        "reference_audio_sha256": audio_hash,
        "reference_text": reference_text,
        "statement": statement or DEFAULT_VOICE_CONSENT_STATEMENT,
        "user": user,
        "consent_confirmed": True
    }
    append_audit_record(record, root)
    return record

def record_synthesis_event(
    output_audio: Path,
    reference_audio: Path | None,
    text: str,
    model_revision: str,
    language: str = "vi",
    consent_confirmed: bool = False,
    cached: bool = False,
    extra: dict | None = None,
    root: Path | None = None
) -> dict:
    ref_hash = file_sha256(reference_audio) if reference_audio else None
    out_hash = file_sha256(output_audio) if output_audio.exists() else None
    is_clone = reference_audio is not None
    record = {
        "id": str(uuid.uuid4()),
        "event": "voice_clone_synthesized" if is_clone else "voice_tts_synthesized",
        "timestamp": now_iso(),
        "model_revision": model_revision,
        "language": language,
        "text_preview": (text[:120] + "...") if len(text) > 120 else text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "reference_audio": str(reference_audio.resolve()) if reference_audio and reference_audio.exists() else (str(reference_audio) if reference_audio else None),
        "reference_audio_sha256": ref_hash,
        "output_audio": str(output_audio.resolve()) if output_audio.exists() else str(output_audio),
        "output_audio_sha256": out_hash,
        "consent_confirmed": consent_confirmed,
        "cached": cached,
        "extra": extra or {}
    }
    append_audit_record(record, root)

    # Ghi file sidecar audit cạnh file audio tổng hợp
    if output_audio.exists():
        sidecar_path = output_audio.with_suffix(output_audio.suffix + ".audit.json")
        sidecar_data = {
            "auditSchema": "whiteboard.voice-audit.v1",
            "auditId": record["id"],
            "timestamp": record["timestamp"],
            "engine": "voxcpm2",
            "modelRevision": model_revision,
            "voiceType": "voice-clone" if is_clone else "standard-tts",
            "language": language,
            "referenceAudioSha256": ref_hash,
            "consentConfirmed": consent_confirmed,
            "outputSha256": out_hash,
            "cached": cached,
            "legalNotice": "Whiteboard Motion AI voice synthesis audit record. Voice cloning requires verified user consent."
        }
        try:
            sidecar_path.write_text(json.dumps(sidecar_data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    return record

def get_voice_audit_log(limit: int = 100, event_type: str | None = None, root: Path | None = None) -> list[dict]:
    log_file = audit_log_path(root)
    if not log_file.is_file():
        return []
    records = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if event_type and item.get("event") != event_type:
                        continue
                    records.append(item)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return records[:limit]
