# Windows 11 installer và Python sidecar

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_windows_installer.ps1
```
Các bước: kiểm version → `tools/fetch_ffmpeg.py` (FFmpeg pin + SHA-256, xem `docs/FFMPEG_BUNDLE.md`) → PyInstaller sidecar `whiteboard-backend-x86_64-pc-windows-msvc.exe` → Tauri build MSI và NSIS → `SHA256SUMS.txt`. Desktop khởi động sidecar qua `tauri-plugin-shell` và truyền `WHITEBOARD_FFMPEG_DIR=<install>\ffmpeg`; máy người dùng không cần cài Python hay FFmpeg.

Model weights, PyTorch, Diffusers và VoxCPM không nằm trong installer. Chúng được Model Manager tải theo lựa chọn người dùng.

Ký code và phát hành: xem `docs/RELEASE.md`. Build không có chứng thư sẽ là UNSIGNED (chỉ dùng cho CI/test).

## Smoke test máy không có NVIDIA (P4.6)
```powershell
powershell -ExecutionPolicy Bypass -File tools/smoke_no_gpu.ps1 -Installer "...\Whiteboard Video_0.1.0_x64-setup.exe"
```
Script cài NSIS im lặng (`/S`), mở app với PATH đã bỏ Python, rồi kiểm tra: sidecar tự chạy, `/hardware` không có NVIDIA, profile `cpu-experimental`, FFmpeg bundled, encoder `libx264` (NVENC thất bại sạch), encode H.264 thật, tạo/lưu project, đóng mở lại app còn dữ liệu, sidecar tắt theo app, gỡ cài đặt không xóa `%LOCALAPPDATA%\WhiteboardVideo\projects`. Report JSON: `benchmarks/smoke-reports/no-gpu-*.json`; exit code 1 nếu có check FAIL.

Workflow `Windows installer` chạy job `smoke-no-gpu` trên GitHub runner `windows-2022` (không có GPU NVIDIA) và upload artifact `no-gpu-smoke-report`. Máy thật iGPU/AMD: chạy cùng script và ghi kết quả vào TEST HANDOFF.
