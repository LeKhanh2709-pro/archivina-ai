---
name: thong-ke-cua-revit
description: "Nút pyRevit HS TKBVTC > Thống kê cửa (2026-11-04): bảng cửa đi + cửa sổ của mặt bằng, gộp theo Type Mark; đã thử bản sao + nút thật, người dùng chưa bấm"
metadata:
  node_type: memory
  type: project
  originSessionId: eab74ad4-3611-4cd8-b85a-0455367f6189
  modified: 2026-11-04T13:47:21.936Z
---

Người dùng yêu cầu 2026-11-04 "1 bảng thống kê các cửa trong mặt bằng, cửa trùng hiện 1 lần", chọn **làm nút riêng** (không sửa bảng trong nút Định vị + tag cửa). Lõi `scripts\dynamo\ThongKeCua_TuDong.py`, skill `thong-ke-cua-revit`.

Revit 2027.3 không gộp cửa đi + cửa sổ vào 1 bảng → nút tạo 2 bảng (đã giải thích cho người dùng). Filter by sheet mặc định tắt vì bảng trên sheet không có mặt bằng sẽ trống.

Tối cùng ngày người dùng đổi yêu cầu: bấm nút phải HIỆN 1 BẢNG (cửa, tên hiện tại, tên đổi, chiều dài, chiều cao) để điền / đổi tên cửa → `lib\arv_bang_cua.py`; "tên cửa" = Type Mark. Yêu cầu đầu "điền tiên cửa" thực ra là "điền tên cửa".

**Why:** người dùng muốn bảng độc lập, không phải bước đặt sheet của [[tag-cua-revit]].

**How to apply:** khi quay lại, hỏi kết quả bấm nút thật (cần Reload pyRevit); nếu người dùng muốn thêm cột (mô tả = Type Comments, STT) hoặc đặt bảng lên sheet thì sửa lõi rồi sinh lại nút bằng builder. Thử như [[revit-2027-dynamo-tu-dong]]; journal phải UTF-8 không BOM.
