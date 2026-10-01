# Reliable API jobs và VoxCPM2 streaming

## Image API
`HttpClient` retry các lỗi tạm thời 408/409/425/429/5xx với exponential backoff, jitter và `Retry-After`. Cancel event dừng trước request, trong download, backoff hoặc polling.

Provider config có thể đặt:
```json
{"estimated_cost_per_image_usd": 0.04, "max_cost_per_job_usd": 0.08}
```
Nếu estimate vượt budget, request bị chặn trước khi gọi API. Progress stages: `cost`, `request`, `backoff`, `download`, `poll`, `write`.

## VoxCPM2 streaming
```python
provider.synthesize_streaming(
    VoiceRequest("Xin chào", Path("voice.wav")),
    cancel_event=cancel_event,
    on_progress=lambda p: print(p.chunks, p.seconds),
)
```
Streaming chỉ ghi WAV 48 kHz. Dữ liệu được ghi vào `*.part.wav` và atomically rename khi hoàn tất; cancel/lỗi xóa file partial. Với job queue, truyền `check_cancelled=ctx.check_cancelled`.
