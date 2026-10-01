# CURRENT

## Đang làm
- P1.6–P1.9 vẫn chờ report từ GPU thật.
- P3.5 chờ report VoxCPM2 từ CPU và GPU thật.

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

## Kiểm tra gần nhất
- 41 Python unit tests thành công, gồm audio cache corruption/invalidation, cache hit không load model và voice benchmark RTF.
- Benchmark harness tạo report JSON với GPU/driver/RAM, revision, elapsed time, peak VRAM, utilization, temperature và output SHA-256.
- GitHub workflow thủ công đã sẵn sàng cho self-hosted runner gắn nhãn `rtx-4060` hoặc `rtx-5060`.
- Source đã đồng bộ lên `HomyHubs/whiteboard-motion`, commit hiện tại `317280b82dd22708e82d146138b74d0b55b1aca1`.
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
