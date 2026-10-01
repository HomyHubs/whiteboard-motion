# VoxCPM2 SRT timeline

```powershell
python tools/voxcpm_srt.py input.srt --output narration.m4a --device auto
```
Compact timeline:
```powershell
python tools/voxcpm_srt.py input.srt --output narration.m4a --retime-out input.tight.srt --gap 0.3 --pause 6=0.8
```
Voice clone yêu cầu reference và xác nhận rõ ràng:
```powershell
python tools/voxcpm_srt.py input.srt --output narration.m4a --reference-audio voice.wav --reference-text "Văn bản mẫu" --confirm-voice-consent
```
Thêm `--video final.mp4` để mux audio vào video. Mỗi cue dùng streaming/cache riêng, sau đó tái sử dụng hàm timeline, retime và mux FFmpeg của pipeline hiện tại.
