# Whiteboard Video Desktop Backend — prototype 0.1

Windows 11 backend prototype bổ sung:
- NVIDIA detection và Qwen profile cho RTX 3060/4060/5060/5060 Ti.
- Model Manager, tải model khi người dùng yêu cầu.
- Qwen-Image-2.1 local provider và external Image API provider.
- VoxCPM2 TTS/voice-clone provider với consent guard.

## Smoke test
```powershell
python -m unittest discover -s backend/tests -v
python -m backend.cli hardware
python -m backend.cli profile
python -m backend.cli models list
```

## Download model khi cần
```powershell
python -m backend.cli models download voxcpm2
python -m backend.cli models download qwen-image-2.1
```

Trước bản production phải thay `revision: main` trong manifest bằng commit SHA đã benchmark.
Qwen-Image-2.1 hiện có research license; không dùng/bundle thương mại nếu chưa có giấy phép riêng.
