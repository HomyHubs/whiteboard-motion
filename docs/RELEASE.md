# Ký code, phát hành và cập nhật (P4.7)

## Phiên bản
Một version duy nhất cho `tauri.conf.json`, `Cargo.toml`, `app/package.json`, `package-lock.json`, `backend/__init__.py`:
```powershell
python tools/release_version.py set 0.2.0
python tools/release_version.py check --tag v0.2.0
```

## Ký code Windows (Authenticode)
- `tools/sign_windows.ps1 <file>`: `signtool sign /fd sha256 /tr <timestamp> /td sha256`, thử lại 3 lần, rồi `signtool verify /pa`.
- Nguồn chứng thư: `WINDOWS_CERTIFICATE_FILE` + `WINDOWS_CERTIFICATE_PASSWORD` (PFX) hoặc `WINDOWS_CERTIFICATE_THUMBPRINT` (chứng thư đã có trong `CurrentUser\My`, ví dụ token EV).
- Không có chứng thư: chỉ cảnh báo `UNSIGNED`, trừ khi `WHITEBOARD_REQUIRE_SIGNING=1` (bản stable) thì dừng build.
- `tools/build_windows_installer.ps1` ký sidecar, rồi truyền `bundle.windows.signCommand` cho Tauri để ký app exe và installer MSI/NSIS. Cuối build tạo `SHA256SUMS.txt`.
- FFmpeg của bên thứ ba không ký lại bằng chứng thư của ta.

Cần mua: chứng thư code signing OV/EV từ CA (DigiCert, Sectigo, SSL.com…) hoặc dùng Azure Trusted Signing. OV mới sẽ bị SmartScreen cảnh báo cho tới khi có đủ uy tín tải xuống; EV giảm cảnh báo ngay.

### Secret trên GitHub
| Secret | Nội dung |
|---|---|
| `WINDOWS_CERTIFICATE` | PFX dạng base64: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("cert.pfx"))` |
| `WINDOWS_CERTIFICATE_PASSWORD` | Mật khẩu PFX |

Không commit PFX/mật khẩu. Workflow xóa file PFX tạm sau khi build.

## Quy trình phát hành
1. Tạo nhánh release, `python tools/release_version.py set X.Y.Z`, cập nhật `CURRENT.md`, merge vào `main`.
2. Đảm bảo workflow **Windows installer** (build + `smoke-no-gpu`) PASS trên commit đó.
3. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
   - `vX.Y.Z` = stable: **bắt buộc ký**, thiếu secret thì workflow fail.
   - `vX.Y.Z-rc.N` = prerelease: cho phép unsigned, đánh dấu prerelease.
4. Workflow **Release**: kiểm version = tag → unit test → build + ký → kiểm chữ ký → smoke test không GPU → tạo **draft** GitHub Release kèm `*-setup.exe`, `*.msi`, `SHA256SUMS.txt`, `FFMPEG-NOTICE.txt`, report smoke.
5. Người phát hành tải installer từ draft, cài thử trên Windows 11 sạch (TEST HANDOFF nhóm F), rồi bấm **Publish**.
6. Rollback: đánh dấu release lỗi là prerelease/xóa asset, phát hành bản vá `X.Y.(Z+1)`; không ghi đè asset của tag đã publish.

## Cập nhật trong app
- Nút **Kiểm tra cập nhật** (UI) gọi `GET /updates`; CLI: `python -m backend.cli check-update`.
- Backend chỉ đọc `releases/latest` của GitHub khi người dùng bấm, trả version mới, link release, link installer và `SHA256SUMS.txt`. **Không tự tải, không tự cài** (app chạy offline, đúng nguyên tắc không tự cập nhật trong `AGENTS.md`).
- Tắt hẳn: `WHITEBOARD_DISABLE_UPDATE_CHECK=1`. Đổi nguồn (mirror nội bộ): `WHITEBOARD_UPDATE_URL`.
- Cài bản mới bằng installer mới; NSIS/MSI nâng cấp tại chỗ, dữ liệu `%LOCALAPPDATA%\WhiteboardVideo` (project, model, cache) được giữ.
- Hướng mở rộng sau: `tauri-plugin-updater` (cần cặp khóa minisign riêng `TAURI_SIGNING_PRIVATE_KEY` và `latest.json`). Chưa bật vì cần quyết định về key và tự động cài đặt.
