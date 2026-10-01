# AGENTS.md — Whiteboard Video Desktop Guidelines

## Mục tiêu
Xây dựng ứng dụng Windows 11 tạo video whiteboard, chạy offline sau khi tải model, hỗ trợ CPU và NVIDIA RTX 20/30/40/50.

## Kiến trúc bắt buộc
- UI desktop không gọi trực tiếp PyTorch. Mọi inference chạy qua Python worker/CLI.
- `backend/providers`: adapter cho voice và image. Không trộn API cloud vào provider local.
- `backend/models`: tải, kiểm tra checksum, quản lý revision và thư mục model.
- Chỉ tải model sau khi người dùng chọn tính năng và chấp nhận dung lượng/license.
- Khi inference offline, luôn ưu tiên đường dẫn local và `local_files_only=True`.
- VoxCPM2 và Qwen-Image-2.1 không được giữ đồng thời trên GPU 8–16 GB.
- Mọi job dài phải có progress, log, cancel và lỗi có thể đọc được.

## Windows 11 / NVIDIA
- RTX 20/30/40 dùng runtime CUDA Standard; RTX 50 dùng runtime Blackwell riêng.
- RTX 20 dùng FP16, không mặc định BF16.
- Profile trọng tâm: RTX 3060 12 GB, 4060 8 GB, 5060 8 GB, 5060 Ti 16 GB.
- Luôn có CPU fallback cho render và voice; Qwen local CPU được đánh dấu experimental.
- Video encoder: `h264_nvenc` nếu có, fallback `libx264`.

## Voice
- Engine local chính: VoxCPM2, EN và VI.
- Hai mode: TTS và zero-shot voice clone.
- Voice clone phải yêu cầu xác nhận người dùng có quyền sử dụng giọng mẫu.
- Reference audio được lưu trong project/voice profile, không upload nếu dùng local.
- Cache phải bao gồm model revision, text, voice/reference hash và tham số sinh.

## Image
- Hai option: external API và Qwen-Image-2.1 local.
- API key chỉ đọc từ Windows Credential Manager hoặc environment; không commit.
- Local provider phải hỗ trợ text-to-image và image editing.
- Ưu tiên tạo asset RGBA tách rời để tự suy ra vùng annotation.
- Profile 8 GB: quantized/offload, mặc định 768 hoặc 1024 px.
- Profile 16 GB: quantized/FP8 khi runtime hỗ trợ, mặc định 1024–1536 px.
- Prompt enhancer là model tùy chọn, không tải mặc định.

## Model và license
- Mỗi model có manifest gồm revision, URL/repo ID, dung lượng dự kiến, SHA-256 nếu dùng file trực tiếp và license.
- VoxCPM2: Apache-2.0.
- Qwen-Image-2.1: research/non-commercial theo license hiện tại; không bundle vào bản thương mại nếu chưa có commercial license.
- Không tự cập nhật model/runtime. Bản phát hành phải pin revision.

## Quy trình task
1. Chọn task nhỏ trong `BACKLOG.md`.
2. Ghi task đang làm và tiêu chí hoàn thành vào `CURRENT.md` trước khi sửa code.
3. Thực hiện thay đổi nhỏ, có test hoặc lệnh smoke test.
4. Cập nhật trạng thái task và ghi quyết định kỹ thuật.
5. Không đánh dấu Done nếu chưa chạy kiểm tra tương ứng.

## Chuẩn code
- Python 3.10+; type hints cho public API.
- Import torch/diffusers/voxcpm theo kiểu lazy để CLI nhẹ vẫn chạy được.
- Không download trong constructor; download là hành động rõ ràng.
- Không dùng bare `except`; lỗi provider phải có hướng xử lý.
- Path phải tương thích Windows và không giả định ổ C:.
