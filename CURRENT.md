# CURRENT

## Đang làm
- P1.6/P1.7 vẫn chờ report từ RTX 4060 và RTX 5060 thật.
- P1.8 Chuẩn bị benchmark RTX 3060 12 GB.
- P1.9 Chuẩn bị benchmark RTX 5060 Ti 16 GB ở 1024/1536 và so sánh Diffusers với ncnn fallback.

## Trạng thái thực thi
- P1.8/P1.9: harness, preflight, PowerShell scripts và self-hosted workflows đã hoàn thành.
- RTX 5060 Ti hỗ trợ benchmark Diffusers mặc định và ncnn fallback để so sánh.
- Các task vẫn `[~]` cho đến khi có report từ GPU thật; không dùng số giả lập.

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
- 17 Python unit tests thành công, gồm job queue, profile, license guard, ncnn validation, backend override và benchmark preflight.
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
