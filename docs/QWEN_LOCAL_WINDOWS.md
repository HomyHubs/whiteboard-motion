# Qwen-Image-2.1 local trên Windows 11

## Backend được chọn
- RTX 3060 12 GB, RTX 4060 8 GB, RTX 5060 8 GB: `ncnn-vulkan` portable. Không cần CUDA/PyTorch; cần driver Vulkan mới và RAM hệ thống phù hợp.
- RTX 5060 Ti 16 GB: `diffusers` mặc định; có thể đổi sang ncnn nếu cần giảm VRAM.

## Revision đã pin
- Official Qwen Diffusers: `d26bb61231c349cf6b7896fa83353113880e1ba3`, 33,134,949,561 bytes.
- ncnn model: `89f21845fe94168a493206d8095956095c454caa`, base download 31,191,736,629 bytes khi bỏ ControlNet.
- ncnn Windows runtime: release `20260928`, SHA-256 `8034bd25a7b467a37f2bd1dc0c405ca95d7366ff2b6870898e4d977c811c018d`.

## Component inventory

| Official Diffusers component | Bytes |
|---|---:|
| Text encoder | 17,534,409,013 |
| Transformer | 14,230,315,061 |
| VAE | 1,350,991,591 |
| Processor và file còn lại | 19,233,896 |
| **Tổng** | **33,134,949,561** |

Bản ncnn base có tổng 31,191,736,629 bytes. ControlNet khoảng 7.55 GB được loại khỏi download mặc định.

## Cài low-VRAM backend
```powershell
python -m backend.cli models accept qwen-image-2.1-ncnn
python -m backend.cli models download qwen-image-2.1-ncnn
python -m backend.cli models download qwenimage-ncnn-windows-runtime
python -m backend.cli models verify qwen-image-2.1-ncnn
```

Qwen Research License hiện không cho sử dụng thương mại nếu chưa có giấy phép riêng. Lệnh `accept` chỉ ghi nhận việc người dùng đã đọc/chấp nhận; không mở rộng quyền license.

## Yêu cầu RAM ncnn trên Windows
Do giới hạn WDDM: `(một nửa RAM hệ thống) + VRAM >= 16 GB`. Khuyến nghị 32 GB RAM; GPU 8 GB có thể chạy với 16 GB RAM nhưng 32 GB an toàn hơn. Model chiếm khoảng 31.2 GB trên đĩa, chưa gồm cache/output.
