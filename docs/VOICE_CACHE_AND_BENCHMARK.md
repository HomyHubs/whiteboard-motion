# VoxCPM2 audio cache và benchmark

## Cache
```python
from backend.cache import AudioCache
provider = VoxCPM2Provider(
    model_path,
    cache=AudioCache(cache_dir),
    model_revision="pinned-hf-sha"
)
```
Cache key thay đổi khi text, ngôn ngữ, seed, model revision, reference audio SHA-256, reference text, settings hoặc định dạng thay đổi. Cache entry lưu checksum riêng và chỉ được khôi phục khi metadata/checksum hợp lệ.

## Benchmark
```powershell
powershell -ExecutionPolicy Bypass -File tools/prepare_voxcpm_benchmark.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_cpu.ps1
powershell -ExecutionPolicy Bypass -File tools/benchmark_voxcpm_rtx5060ti.ps1
```
Gửi file JSON trong `benchmarks/voice-reports/` để chốt P3.5. Không commit output WAV hoặc report chứa đường dẫn máy cá nhân.
