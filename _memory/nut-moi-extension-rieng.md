---
name: nut-moi-extension-rieng
description: "Nút pyRevit mới / thử nghiệm làm thành extension riêng gỡ được, không sửa ARVTools.extension (tab Archivina) khi chưa được bảo"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9e633091-54cc-4e0d-803e-ceed8b83d097
  modified: 2026-11-13T04:38:35.086Z
---

Người dùng (2026-11-13), khi được hỏi chọn icon để thêm nút "Hồ sơ đã duyệt" vào panel HS TKBVTC của tab Archivina, trả
lời: "sinh nút mới ở trên thanh công cụ đi, đừng động gì đến archivina, để t có thể gỡ".

**Why:** người dùng muốn gỡ được nút mới mà không ảnh hưởng bộ Archivina đang dùng (và đang đóng gói cho máy khác).

**How to apply:** nút mới chưa được duyệt đưa vào Archivina → làm extension riêng trong `D:\AI\scripts\pyrevit\`
(đã là Extension Search Path, không phải sửa cấu hình pyRevit), tab riêng, viết tay, không qua `build_from_dynamo.py`.
Cần lõi / lib của Archivina thì chỉ đọc + chạy (thêm `ARVTools.extension\lib` vào `sys.path`, thay hàm lúc chạy), kể cả
bản sửa lõi thì để bản riêng trong extension mới. Kiểm `git status` thấy `ARVTools.extension` sạch trước khi báo xong.
Phạm vi (diễn giải của Claude): áp cho nút mới / thử nghiệm; sửa lỗi nút Archivina khi người dùng yêu cầu thì vẫn sửa ở
Archivina. Mẫu: [[nut-ho-so-duyet]]. Liên quan [[anh-duyet-truoc-khi-build]], [[pyrevit-arvtools-revit2027]].
