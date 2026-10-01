# FFmpeg đóng gói, NVENC và fallback libx264 (P4.5)

## Bản FFmpeg được bundle
| Mục | Giá trị |
|---|---|
| Build | `9.0.2-essentials_build-www.gyan.dev` (static, Windows x64) |
| Nguồn | `https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.zip` |
| SHA-256 | `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba` |
| License | GPL-3.0-or-later (`--enable-gpl --enable-version3`, có libx264/libx265) |
| Encoder dùng | `h264_nvenc` (NVIDIA) → `libx264` (CPU) |
| File đưa vào installer | `ffmpeg.exe`, `ffprobe.exe`, `LICENSE.txt`, `BUILD-README.txt`, `NOTICE.txt`, `ffmpeg-bundle.json` |

Manifest pin nằm ở `tools/ffmpeg-manifest.json`. Không tự cập nhật FFmpeg: đổi version phải sửa manifest (URL + SHA-256) trong một commit riêng.

```powershell
python tools/fetch_ffmpeg.py            # tải, kiểm SHA-256, chép vào app/src-tauri/resources/ffmpeg/
python tools/fetch_ffmpeg.py --archive D:\ffmpeg-9.0.2-essentials_build.zip   # dùng file đã tải sẵn
```
`tools/build_windows_installer.ps1` tự gọi bước này. Thư mục `resources/ffmpeg/` bị `.gitignore`, không commit binary.

## Quyết định license
- libx264 là GPL nên bản FFmpeg có libx264 bắt buộc là GPL. Ta **không link** FFmpeg vào app; chỉ chạy `ffmpeg.exe`/`ffprobe.exe` như chương trình riêng (aggregate). Code của app vẫn MIT.
- Installer kèm `LICENSE.txt` (GPLv3), `NOTICE.txt` (link source chính xác: commit FFmpeg, tarball release, build script Gyan, x264) và lời đề nghị cung cấp source 3 năm. Release workflow đính kèm thêm `FFMPEG-NOTICE.txt`.
- Không dùng build `--enable-nonfree`. Báo cáo `/media` trả `license` và `nonfree` để kiểm tra.
- Nếu sau này cần installer không chứa thành phần GPL: thay bằng build LGPL (không libx264) và dùng `h264_nvenc`/`h264_mf` (Media Foundation) làm encoder; khi đó cần đổi fallback trong `backend/media/ffmpeg.py`.

## Chọn encoder
`backend/media/ffmpeg.py`:
1. Tìm FFmpeg: `WHITEBOARD_FFMPEG_DIR` (Tauri set = `<install>\ffmpeg`) → thư mục `ffmpeg` cạnh sidecar → `vendor/ffmpeg` hoặc `app/src-tauri/resources/ffmpeg` (dev) → `PATH`.
2. `h264_nvenc` chỉ được chọn khi encode thử 2 frame thành công (build Gyan luôn liệt kê NVENC kể cả khi máy không có NVIDIA).
3. Nếu NVENC lỗi khi chạy thật (hết session, driver cũ…), lệnh được chạy lại bằng `libx264`.
4. Ép encoder: `WHITEBOARD_VIDEO_ENCODER=auto|nvenc|x264`.

Tham số: NVENC `-preset p5 -tune hq -rc vbr -cq 23 -b:v 0`; libx264 `-preset medium -crf 20`; luôn `yuv420p`.

Kiểm tra nhanh:
```powershell
python -m backend.cli media        # JSON: đường dẫn, nguồn (bundled/env/path), license, nvencUsable, encoder
curl.exe http://127.0.0.1:8765/media
```
Các script `scripts/stream_render.py`, `scripts/merge_scenes.py`, `scripts/tts_narration.py`, `tools/voxcpm_srt.py` dùng chung cơ chế này qua `scripts/media_tools.py`.
