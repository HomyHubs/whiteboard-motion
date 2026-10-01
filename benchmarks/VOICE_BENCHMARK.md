# VoxCPM2 benchmark

Chuẩn bị model:
```powershell
powershell -ExecutionPolicy Bypass -File tools/prepare_voxcpm_benchmark.ps1
```
Chạy CPU hoặc GPU:
```powershell
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_cpu.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_rtx3060.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_rtx4060.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_rtx5060.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_rtx5060ti.ps1
```
Report gồm model revision, load time, synthesis time, audio duration, real-time factor (RTF), peak VRAM, utilization, temperature và output SHA-256. RTF < 1 nghĩa là tạo nhanh hơn thời lượng âm thanh.
