# CURRENT

## Đang làm
- P1.6 Benchmark RTX 4060 8 GB ở 768/1024.
- P1.7 Benchmark RTX 5060 8 GB và xác nhận driver/Vulkan Blackwell.
- Đồng bộ source lên `HomyHubs/whiteboard-motion` để chạy test trên Windows 11.

## Trạng thái thực thi
- Có thể hoàn thiện benchmark harness, report schema và workflow ngay.
- Số liệu hiệu năng thật chỉ được ghi sau khi chạy trên đúng GPU; không dùng số giả lập.

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
- 13 Python unit tests thành công, gồm job queue, profile, license guard và ncnn validation.
- Tải thật Windows ncnn runtime 20260928, xác minh SHA-256 và tìm thấy executable 14,456,320 bytes.
- `npm run build` thành công.
- Chưa tải model ncnn 31.2 GB hoặc chạy inference vì môi trường không có GPU Windows.
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
- Low-VRAM Qwen 8 GB mới có cấu hình offload; chưa tích hợp GGUF backend production.
- Chưa benchmark trên GPU thật.
- Model revision trong manifest cần pin SHA sau khi kiểm thử acceptance.
