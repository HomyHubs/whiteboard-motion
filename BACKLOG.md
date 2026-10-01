# BACKLOG

Quy ước: `[ ]` Todo · `[~]` In progress · `[x]` Done

## P0 — Nền tảng
- [x] P0.1 Tạo cấu trúc backend provider/model manager và CLI.
- [x] P0.2 Phát hiện GPU NVIDIA bằng `nvidia-smi` và chọn hardware profile.
- [x] P0.3 Thêm profile cho RTX 3060, 4060, 5060 8 GB và 5060 Ti 16 GB.
- [x] P0.4 Thêm Windows bootstrap/check script.
- [x] P0.5 Tạo job queue có progress/cancel và khóa GPU liên tiến trình.
- [x] P0.6 Tích hợp backend vào UI desktop Tauri.

## P1 — Qwen-Image-2.1 local
- [x] P1.1 Tạo provider Diffusers lazy-load, local-only sau khi tải model.
- [x] P1.2 Thêm text-to-image, image editing và unload VRAM.
- [x] P1.3 Thêm model manifest và downloader Hugging Face có revision pin.
- [x] P1.4 Xác nhận revision model production và dung lượng từng component.
- [x] P1.5 Backend quantized low-VRAM cho card 8 GB (GGUF/ComfyUI hoặc runtime tương đương).
- [~] P1.6 Benchmark RTX 4060 8 GB: 768/1024, peak VRAM, thời gian — harness đã sẵn sàng, chờ máy thật.
- [~] P1.7 Benchmark RTX 5060 8 GB với CUDA Blackwell runtime — harness đã sẵn sàng, chờ máy thật.
- [~] P1.8 Benchmark RTX 3060 12 GB — harness/preflight đã sẵn sàng, chờ report máy thật.
- [~] P1.9 Benchmark RTX 5060 Ti 16 GB: 1024/1536 — Diffusers/ncnn harness đã sẵn sàng, chờ report máy người dùng.
- [x] P1.10 Tạo asset RGBA và tự động sinh annotation bounds.
- [x] P1.11 Prompt enhancer tùy chọn.

## P2 — Image API
- [x] P2.1 Adapter HTTP API cấu hình endpoint/model/header.
- [x] P2.2 Tích hợp Windows Credential Manager.
- [x] P2.3 Mapping response cho OpenAI-compatible và các nhà cung cấp cụ thể.
- [x] P2.4 Retry/backoff, progress và kiểm soát chi phí.

## P3 — VoxCPM2
- [x] P3.1 Provider cơ bản cho TTS và voice clone.
- [x] P3.2 Voice profile + xác nhận consent.
- [x] P3.3 Streaming generation và cancel.
- [x] P3.4 Cache audio theo model/reference/text/settings.
- [~] P3.5 Benchmark CPU, RTX 3060/4060/5060/5060 Ti — harness/workflow đã sẵn sàng, chờ report máy thật.
- [x] P3.6 Timeline/SRT integration với pipeline hiện tại.

## P4 — Desktop/Packaging
- [x] P4.1 Tauri + React project shell.
- [x] P4.2 Model Manager UI: dung lượng, license, download, verify, delete.
- [ ] P4.3 Project/scene editor và tích hợp `assets/preview.html`.
- [ ] P4.4 Installer Windows 11 và Python sidecar.
- [ ] P4.5 Bundle FFmpeg phù hợp license; NVENC + libx264 fallback.
- [ ] P4.6 Smoke test trên máy không có NVIDIA GPU.
- [ ] P4.7 Ký code và quy trình release/update.

## P5 — An toàn và phát hành
- [ ] P5.1 Màn hình consent voice clone và audit metadata.
- [ ] P5.2 Hiển thị/chấp nhận license model trước download.
- [ ] P5.3 Kiểm tra commercial license của Qwen-Image-2.1 trước bản thương mại.
- [ ] P5.4 Secret scan, dependency scan và SBOM.
