---
name: anh-duyet-truoc-khi-build
description: "Thay đổi giao diện nút / ribbon / bố cục: gửi ảnh xem trước, chờ người dùng duyệt rồi mới sửa builder và build"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 7f619c8b-49e4-4b39-8c51-02fcd1eabb63
  modified: 2026-11-05T02:15:48.057Z
---

Mọi thay đổi giao diện (ribbon pyRevit, nút, icon, bố cục bảng, tag...) phải dựng ẢNH XEM TRƯỚC gửi người dùng, chờ duyệt
rồi mới sửa code builder / build. Người dùng chặn giữa chừng 2026-11-05 khi Claude đang sửa `build_from_dynamo.py` để thu
gọn 5 panel thành nút xổ: "GỬI T ẢNH TRƯỚC, T DUYỆT RỒI MỚI BUILD".

**Why:** người dùng muốn chốt hình thức trước, tránh build xong lại phải sửa / Reload pyRevit nhiều lần.
**How to apply:** vẽ ảnh bằng WPF (mẫu `scripts\pyrevit\icons\nguon\Program.cs`, bản thu gọn `_tmp\ribbon_thugon\`),
không sửa file nguồn trước khi duyệt. Liên quan [[tag-cua-revit]], [[pyrevit-arvtools-revit2027]].
