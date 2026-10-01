# CURRENT

## Đang làm
- P1.6–P1.9 và P3.5 vẫn chờ report phần cứng thật.
- P4.4 chờ Windows CI tạo MSI/NSIS và Agent test cài đặt trên Windows 11.
- P4.5/P4.6/P4.7 code xong, chờ Windows CI (build + `smoke-no-gpu`) và chứng thư code signing.

## Task vừa xử lý — P4.5, P4.6, P4.7
Tiêu chí hoàn thành:
- P4.5: installer chứa `ffmpeg/ffmpeg.exe`, `ffprobe.exe`, LICENSE/NOTICE; `/media` báo `source=bundled|env`; NVENC chỉ chọn khi encode thử thành công, lỗi runtime tự chạy lại bằng libx264.
- P4.6: job `smoke-no-gpu` (runner `windows-2022`, không NVIDIA) PASS toàn bộ check của `tools/smoke_no_gpu.ps1`.
- P4.7: build ký được bằng PFX/thumbprint, tag stable bắt buộc ký, draft release có installer + `SHA256SUMS.txt`; app có kiểm tra cập nhật thủ công.

Đã làm:
- `backend/media/ffmpeg.py`: tìm FFmpeg (`WHITEBOARD_FFMPEG_DIR` → cạnh sidecar → source tree → PATH), thử NVENC 2 frame, fallback libx264, `WHITEBOARD_VIDEO_ENCODER=auto|nvenc|x264`; CLI `media`, API `/media`; UI hiển thị encoder.
- `scripts/media_tools.py`; `stream_render.py`, `merge_scenes.py`, `tts_narration.py`, `tools/voxcpm_srt.py` dùng FFmpeg bundled + encoder chung.
- FFmpeg pin: Gyan `9.0.2-essentials_build`, SHA-256 `60f46726…47ba`, GPL-3.0-or-later; `tools/fetch_ffmpeg.py` tạo `NOTICE.txt` + `ffmpeg-bundle.json`; Tauri `bundle.resources` → `<install>\ffmpeg`, `main.rs` truyền `WHITEBOARD_FFMPEG_DIR`. Chi tiết license: `docs/FFMPEG_BUNDLE.md`.
- Thêm bộ icon `app/src-tauri/icons` (thiếu `icons/icon.ico` là nguyên nhân khả dĩ khiến CI run `36904470333` fail ở bước Tauri build; log CI cần quyền đọc nên chưa xác nhận).
- `tools/smoke_no_gpu.ps1` + job `smoke-no-gpu` trong `windows-installer.yml`; workflow còn chạy unit test trước khi build.
- `tools/sign_windows.ps1`, `tools/release_version.py`, `.github/workflows/release.yml`, `backend/updates.py` (`/updates`, CLI `check-update`, nút Kiểm tra cập nhật; không tự tải/cài). Quy trình: `docs/RELEASE.md`.

Kiểm tra đã chạy (Linux, không có NVIDIA, FFmpeg 7.0.2 không có NVENC):
- 69 unit test PASS (thêm `test_media`, `test_updates`, `test_release`, `test_no_gpu`).
- `python -m backend.cli media` → encoder `libx264`, `nvencUsable=false`; `/health`, `/media`, `/updates` trả JSON.
- `transcode_h264` và `merge_scenes.py` encode H.264 thật bằng libx264.
- `fetch_ffmpeg.py --archive` với archive đã tải: SHA-256 khớp, giải nén đủ file, lần hai báo up to date.
- `npm run build` thành công; PowerShell parser không lỗi cú pháp cho 4 script `.ps1`; `sign_windows.ps1` bỏ qua khi không có cert và dừng khi `WHITEBOARD_REQUIRE_SIGNING=1`.
- Chưa chạy: Tauri/Cargo build Windows, cài installer thật, ký thật (chưa có chứng thư).
- Checklist **TEST HANDOFF** vẫn bắt buộc; Agent kiểm thử ghi kết quả trực tiếp vào file này.

## Task vừa xử lý — P4.3 và P4.4
- P4.3 hoàn thành: project store trong app-data, ID validation chống path traversal và atomic JSON writes.
- UI tạo/chọn project, tạo/sửa scene manifest và nhúng `assets/preview.html` trong iframe.
- P4.4 đã có PyInstaller sidecar, Tauri externalBin, PowerShell build MSI/NSIS và Windows CI artifact.
- Sidecar bundle control plane/downloader/project API; không bundle model weights hoặc ML runtime nặng.
- P4.4 vẫn `[~]` cho đến khi Windows artifact được cài và smoke test thành công.
- Windows installer CI run cho commit `56ee7044bd396fe3f3e08a480f4a5c6333f1d278`: `https://github.com/HomyHubs/whiteboard-motion/actions/runs/36904470333` — trạng thái lúc ghi: `in_progress`. Agent test cập nhật conclusion/artifact vào bảng TEST HANDOFF.

## Hai task vừa hoàn thành — P3.6 và P4.2
- VoxCPM2 tạo audio từng SRT cue bằng streaming/cache, sau đó dùng timeline/build-track/retime/mux FFmpeg hiện có.
- Hỗ trợ compact retime, pause riêng, voice clone consent và video mux.
- Model Manager UI hiển thị revision, dung lượng, mục đích, license và trạng thái cài đặt.
- Accept license, Download background job, Verify và Delete đều có API/UI; không tự động tải model.
- Download job xuất hiện trong bảng Jobs, hỗ trợ theo dõi và cancel.

## Task vừa xử lý — P3.4 và P3.5
- P3.4 hoàn thành: cache key gồm engine/model revision/text/language/seed/reference SHA-256/reference text/settings/format.
- Cache restore/store atomic, kiểm tra audio SHA-256 và tự miss khi metadata/file bị đổi.
- Streaming và non-streaming cùng dùng cache; cache hit không load hoặc gọi model.
- P3.5 đã có harness, PowerShell scripts và self-hosted workflow cho CPU, RTX 3060/4060/5060/5060 Ti.
- Report gồm load time, synthesis time, audio duration, RTF, peak VRAM, utilization, temperature và output SHA-256.
- P3.5 vẫn `[~]` đến khi chạy trên phần cứng thật.

## Hai task vừa hoàn thành — P2.4 và P3.3
- HTTP client retry lỗi tạm thời 408/409/425/429/5xx, exponential backoff, jitter và `Retry-After`.
- Cancel hoạt động trước request, trong backoff, download và Replicate polling.
- Image API progress stages: cost/request/backoff/download/poll/write.
- Cost guard chặn request trước khi gọi API nếu estimate vượt budget cấu hình.
- VoxCPM2 streaming ghi WAV 48 kHz theo chunk, báo chunks/samples/seconds và hỗ trợ job cancellation.
- Dùng file `*.part.wav`, chỉ rename khi hoàn tất; cancel/lỗi sẽ xóa partial.

## Hai task vừa hoàn thành — P2.2 và P2.3
- Windows Credential Manager adapter dùng `CredWriteW`, `CredReadW`, `CredDeleteW`; không lưu key trong project/config.
- CLI `credentials set/check/delete`; lệnh set dùng hidden `getpass`.
- Provider config chỉ lưu endpoint, model và credential target.
- Adapter/mapping riêng cho OpenAI-compatible/Together, Stability AI v2 và Replicate prediction polling.
- Giữ `ApiImageProvider` làm compatibility alias cho code cũ.
- Thêm config mẫu và `docs/IMAGE_API_PROVIDERS.md`.

## Hai task vừa hoàn thành — P1.10 và P1.11
- Pipeline ghép PNG RGBA lên canvas kem, tính alpha bounds và sinh annotation theo sequence/timeline.
- Kiểm tra asset vượt canvas, asset hoàn toàn trong suốt và cảnh báo overlap.
- CLI `tools/compose_rgba_scene.py`, manifest mẫu và tài liệu sử dụng.
- Prompt enhancer T2I/I2I lazy-load, parse JSON answer, presence penalty đúng profile và unload VRAM.
- Pin hai model enhancer cùng revision/dung lượng/license; không tải mặc định.
- Runtime enhancer được tách riêng trong `requirements-prompt-enhancer.txt`.

## Hai task vừa hoàn thành — P1.4 và P1.5
- Pin official Qwen-Image-2.1 revision `d26bb61231c349cf6b7896fa83353113880e1ba3` với inventory 33,134,949,561 bytes.
- Pin ncnn model revision `89f21845fe94168a493206d8095956095c454caa`; tải base 31,191,736,629 bytes và bỏ ControlNet không cần thiết.
- Pin Windows ncnn runtime release `20260928` cùng SHA-256 của archive.
- Model Manager hỗ trợ license acceptance, revision cố định, download resume/checksum cho archive và verify inventory.
- Thêm `QwenImage21NcnnProvider` cho text-to-image, image editing, multi-reference và RGBA.
- RTX 3060/4060/5060 chọn ncnn/Vulkan; RTX 5060 Ti 16 GB chọn Diffusers.
- Thêm hướng dẫn `docs/QWEN_LOCAL_WINDOWS.md`.

## Hai task vừa hoàn thành
- P0.5: job queue có trạng thái, progress, cooperative cancel và file lock GPU liên tiến trình.
- P0.6: HTTP backend cục bộ và Tauri + React shell hiển thị hardware, Qwen profile, models và jobs.
- P4.1 cũng hoàn thành ở mức source shell; frontend production build đã chạy thành công.

## TEST HANDOFF — Agent kiểm thử phải cập nhật phần này

### Quy tắc
1. Pull đúng commit mới nhất từ `HomyHubs/whiteboard-motion`; ghi SHA đang test.
2. Không sửa code trong lúc test. Nếu cần sửa, tạo commit riêng và ghi SHA mới.
3. Chạy từng nhóm test bên dưới; không ghi PASS nếu không có command/log hoặc file report.
4. Ghi kết quả trực tiếp vào mục **Kết quả test từ Agent khác** trong file này rồi commit/push.
5. Với lỗi: ghi command, exit code, stack trace rút gọn, bước tái hiện và đường dẫn artifact/report.
6. Không commit API key, voice reference riêng tư, model weights, output WAV/PNG lớn hoặc đường dẫn chứa thông tin nhạy cảm.

### A. Smoke test bắt buộc
```powershell
python -m unittest discover -s backend/tests -v
python -m backend.cli hardware
python -m backend.cli profile
python -m backend.cli models list
powershell -ExecutionPolicy Bypass -File tools/restore_assets.ps1
cd app
npm install --no-audit --no-fund
npm run build
cd ..
```
Kỳ vọng: toàn bộ unit test PASS; hardware/profile/models trả JSON; asset checksum hợp lệ; Vite build thành công.

### B. Backend và Model Manager UI
```powershell
python -m backend.cli serve
# terminal khác
curl.exe http://127.0.0.1:8765/health
curl.exe http://127.0.0.1:8765/models
cd app
npm run dev
```
Kiểm tra thủ công:
- UI báo Backend online và hiển thị đúng GPU/profile.
- Model chưa accept license không thể Download.
- Accept license chỉ sau confirmation; Download tạo background job.
- Verify trả `ok=true` với model đầy đủ; Delete yêu cầu confirmation và cập nhật UI.
- Cancel job không làm backend treo.

### C. Windows Credential Manager
```powershell
python -m backend.cli credentials set openai
python -m backend.cli credentials check openai
cmdkey /list | findstr WhiteboardVideo
python -m backend.cli credentials delete openai
python -m backend.cli credentials check openai
```
Dùng key test giả, không dùng production key. Kỳ vọng: configured chuyển `true` rồi `false`; secret không xuất hiện trong console/history/config.

### D. VoxCPM2 SRT timeline — cần model khoảng 5 GB
```powershell
python -m backend.cli models download voxcpm2
python tools/voxcpm_srt.py path\input.srt --output path\narration.m4a --device auto
python tools/voxcpm_srt.py path\input.srt --output path\narration-tight.m4a --retime-out path\input.tight.srt --gap 0.3
```
Kiểm tra:
- Mỗi cue có file WAV hợp lệ; lần chạy hai báo cache hit/không load lại model.
- Audio khớp thứ tự cue; `input.tight.srt` tăng thời gian đơn điệu, không chồng cue.
- Không còn `*.part.wav` sau thành công/cancel.
- Nếu test clone voice, chỉ dùng giọng được phép và bắt buộc `--confirm-voice-consent`.

### E. Benchmark trên máy người dùng RTX 5060 Ti 16 GB
```powershell
powershell -ExecutionPolicy Bypass -File tools/prepare_voxcpm_benchmark.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_rtx5060ti.ps1
# Qwen: chọn một backend đã tải model
powershell -ExecutionPolicy Bypass -File tools/benchmark_rtx5060ti.ps1 -Backend ncnn-vulkan
```
Đính kèm JSON từ `benchmarks/voice-reports/` và `benchmarks/reports/`. Ghi driver, RAM, VRAM, backend, resolution, peak VRAM, thời gian và RTF.

### F. Windows sidecar và installer
```powershell
powershell -ExecutionPolicy Bypass -File tools/build_backend_sidecar.ps1
powershell -ExecutionPolicy Bypass -File tools/build_windows_installer.ps1
```
Sau đó cài cả NSIS hoặc MSI trên Windows 11 sạch và kiểm tra:
- App mở mà không cần Python trong PATH.
- Sidecar tự khởi động; `/health`, Projects và Models hoạt động.
- Tạo project/scene, đóng/mở app và dữ liệu vẫn tồn tại trong app-data.
- Annotation preview mở trong app.
- Uninstall không xóa model/project người dùng ngoài ý muốn.
Ghi tên installer, kích thước, SHA-256, thời gian build, log lỗi và đường dẫn artifact. P4.4 chỉ được đánh dấu Done sau khi nhóm này PASS.

### G. Smoke test máy không có NVIDIA (P4.6)
```powershell
powershell -ExecutionPolicy Bypass -File tools/smoke_no_gpu.ps1 -Installer "<đường dẫn>\Whiteboard Video_0.1.0_x64-setup.exe"
```
Chạy trên máy không có NVIDIA (CI `smoke-no-gpu` hoặc laptop iGPU/AMD). Đính kèm `benchmarks/smoke-reports/no-gpu-*.json`. Kỳ vọng `RESULT=PASS`, encoder `libx264`, FFmpeg `source=bundled|env`.

### H. Release dry-run (P4.7)
Đẩy tag prerelease `v0.1.1-rc.1` sau khi đã `python tools/release_version.py set 0.1.1-rc.1`; kiểm tra workflow Release tạo draft có `*-setup.exe`, `*.msi`, `SHA256SUMS.txt`, `FFMPEG-NOTICE.txt`. Khi có chứng thư: `Get-AuthenticodeSignature` phải `Valid`.

### Kết quả test từ Agent khác
> Agent kiểm thử thay các dòng `PENDING`; không xóa hướng dẫn phía trên.

| Ngày | Commit SHA | Máy/OS/GPU/RAM | Nhóm | Kết quả | Exit code | Artifact/report | Ghi chú/lỗi |
|---|---|---|---|---|---:|---|---|
| PENDING | PENDING | Windows 11 / PENDING | A. Smoke | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | Windows 11 / PENDING | B. Model Manager UI | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | Windows 11 / PENDING | C. Credential Manager | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | Windows 11 / RTX 5060 Ti 16 GB | D. VoxCPM SRT | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | Windows 11 / RTX 5060 Ti 16 GB | E. Benchmarks | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | Windows 11 sạch | F. Sidecar + MSI/NSIS | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | Windows, không NVIDIA | G. No-GPU smoke | PENDING | PENDING | PENDING | PENDING |
| PENDING | PENDING | GitHub Actions | H. Release dry-run | PENDING | PENDING | PENDING | PENDING |

### Yêu cầu review sau test
- **Blocker:** PENDING
- **Major:** PENDING
- **Minor:** PENDING
- **Đề xuất thay đổi:** PENDING
- **Có thể tiếp tục task kế tiếp:** PENDING (Yes/No + lý do)

## Kiểm tra gần nhất
- 47 Python unit tests thành công, gồm project path traversal/atomic write; project/preview HTTP smoke test và React build thành công.
- Benchmark harness tạo report JSON với GPU/driver/RAM, revision, elapsed time, peak VRAM, utilization, temperature và output SHA-256.
- GitHub workflow thủ công đã sẵn sàng cho self-hosted runner gắn nhãn `rtx-4060` hoặc `rtx-5060`.
- Source được đồng bộ liên tục lên `HomyHubs/whiteboard-motion`; Agent test phải ghi commit SHA thực tế trong bảng TEST HANDOFF.
- Chưa có số benchmark thật vì môi trường hiện tại không có Windows/NVIDIA GPU phù hợp.
- Chưa chạy native `cargo tauri build` vì môi trường làm việc không có Rust/Cargo.

## Vừa hoàn thành
- P0.1–P0.4: backend skeleton, CLI, hardware detection, Windows scripts.
- P1.1–P1.3: Qwen-Image-2.1 Diffusers provider và model manager.
- P2.1: generic external image API adapter.
- P3.1–P3.2: VoxCPM2 TTS/clone provider và consent guard.

## Kiểm tra đã chạy
- `python -m unittest discover -s backend/tests -v`
- `python -m backend.cli hardware`
- `python -m backend.cli models list`

## Giới hạn hiện tại
- Đã có Tauri/React shell; chưa có native installer và chưa build bằng Cargo trên Windows.
- Đã tích hợp ncnn/Vulkan low-VRAM, nhưng còn ở giai đoạn early-development upstream và cần acceptance test trên từng GPU.
- P1.6/P1.7 vẫn In progress cho tới khi report được tạo trên RTX 4060 và RTX 5060 thật.
- Binary demo asset không push trực tiếp qua MCP; chạy `tools/restore_assets.ps1` để tải asset đã pin và kiểm tra SHA-256.
