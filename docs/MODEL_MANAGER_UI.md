# Model Manager UI

Backend endpoints:
- `GET /models`
- `POST /models/{id}/accept`
- `POST /models/{id}/download` — background job
- `POST /models/{id}/verify`
- `DELETE /models/{id}`

UI hiển thị revision, dung lượng, mục đích, license và trạng thái. Model có research license phải được chấp nhận trước khi nút Download hoạt động. Download không chạy tự động; job có thể theo dõi/hủy trong bảng Jobs. Xóa model không xóa acceptance record, nhưng revision/license thay đổi sẽ buộc chấp nhận lại.
