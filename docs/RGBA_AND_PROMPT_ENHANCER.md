# RGBA scene composition và Prompt Enhancer

## RGBA assets
Yêu cầu Qwen tạo từng nhân vật/đồ vật dưới dạng PNG RGBA riêng. Khai báo vị trí/thứ tự trong manifest rồi chạy:
```powershell
python tools/compose_rgba_scene.py project/scene.manifest.json --image project/scene.png --annotation project/scene.annotation.json
```
Alpha bounds được chuyển thành `region`; canvas mặc định dùng nền kem `#F5EBD7`. Tool báo overlap, asset trong suốt và từ chối asset vượt canvas.

## Optional Prompt Enhancer
Hai model 9B riêng biệt, không tải mặc định:
```powershell
python -m backend.cli models accept qwen-image-2.1-pe-t2i
python -m backend.cli models download qwen-image-2.1-pe-t2i
python tools/enhance_prompt.py "A fox holding an umbrella" --task t2i
```
Edit mode dùng model `qwen-image-2.1-pe-i2i` và ít nhất một `--image`. Mỗi model khoảng 18.84 GB; cần unload trước khi nạp Qwen-Image trên card 16 GB.
