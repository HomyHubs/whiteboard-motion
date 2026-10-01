# GPU benchmarks

Các report trong `benchmarks/reports/` phải được tạo trên GPU thật bằng `tools/benchmark_qwen.py`; không nhập số thủ công.

## RTX 4060 8 GB
```powershell
powershell -ExecutionPolicy Bypass -File tools/benchmark_rtx4060.ps1
```

## RTX 5060 8 GB
```powershell
powershell -ExecutionPolicy Bypass -File tools/benchmark_rtx5060.ps1
```

Mỗi report ghi GPU/driver/VRAM/RAM, revision model, backend profile, thời gian, peak VRAM, GPU utilization, temperature, output SHA-256 và lỗi nếu có. Dùng `--steps 40` cho acceptance benchmark cuối; 20 steps dùng cho smoke/performance iteration.

## RTX 3060 12 GB
```powershell
powershell -ExecutionPolicy Bypass -File tools/benchmark_rtx3060.ps1
```

## RTX 5060 Ti 16 GB
Diffusers mặc định:
```powershell
powershell -ExecutionPolicy Bypass -File tools/benchmark_rtx5060ti.ps1
```
Ncnn fallback:
```powershell
powershell -ExecutionPolicy Bypass -File tools/benchmark_rtx5060ti.ps1 -Backend ncnn-vulkan
```

Trước lần chạy đầu, tải model tương ứng:
```powershell
powershell -ExecutionPolicy Bypass -File tools/prepare_qwen_benchmark.ps1 -Backend ncnn-vulkan
# hoặc -Backend diffusers
```
Dùng `python tools/benchmark_qwen.py ... --preflight-only` để kiểm tra GPU/profile/model mà không inference.
