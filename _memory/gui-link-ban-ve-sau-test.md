---
name: gui-link-ban-ve-sau-test
description: Sau khi chạy thử xong luôn gửi link (đường dẫn bấm được) tới bản vẽ kết quả DWG/DXF/PNG
metadata:
  node_type: memory
  type: feedback
  originSessionId: 76f2a5b5-b8aa-4917-aa80-c955d362948c
  modified: 2026-10-28T09:53:58.108Z
---

Sau mỗi lần chạy thử (test) skill / script tạo bản vẽ, luôn gửi người dùng link bấm được tới bản vẽ kết quả (DWG trước, kèm DXF / PNG nếu có), dạng markdown link đường dẫn tương đối từ `D:\AI`, vd. `[VK_4210_so3.dwg](file mau/05_VachKinh/VK_4210_so3.dwg)`.

**Why:** người dùng yêu cầu 2026-10-28 (sau khi thử skill [[chia-do-vach-kinh]]) để mở bản vẽ kiểm tra ngay, không phải tự tìm.

**How to apply:** áp cho mọi lần test có tạo file bản vẽ (AutoCAD, Revit bản sao, ảnh PNG xem lại), cả bản ở `_tmp`; đặt link ngay trong tin nhắn cuối.
