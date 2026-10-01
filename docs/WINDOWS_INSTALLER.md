# Windows 11 installer và Python sidecar

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_windows_installer.ps1
```
Quy trình tạo `whiteboard-backend-x86_64-pc-windows-msvc.exe` bằng PyInstaller, sau đó Tauri đóng gói MSI và NSIS. Desktop khởi động sidecar qua `tauri-plugin-shell`; máy người dùng không cần cài Python.

Model weights, PyTorch, Diffusers và VoxCPM không nằm trong installer. Chúng được Model Manager tải theo lựa chọn người dùng. Sidecar chỉ bundle backend control plane, model downloader, project store và API server.

Installer chưa ký code. Không phát hành production trước P4.7. Kết quả Windows CI/installer smoke test phải được ghi vào TEST HANDOFF trong `CURRENT.md`.
