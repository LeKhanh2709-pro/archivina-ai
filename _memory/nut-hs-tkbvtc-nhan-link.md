---
name: nut-hs-tkbvtc-nhan-link
description: 9 nút HS TKBVTC đọc được đối tượng trong file link Revit (khối Link_chung.py); bảng có link phải vẽ drafting; dim vào link reference bị Revit bỏ → bám nét ẩn
metadata:
  node_type: memory
  type: project
  originSessionId: f537cbf9-3208-4457-a0c8-a8722732538f
  modified: 2026-11-10T13:46:41.225Z
---

2026-11-10: thử trên bản sao HQV tháp B Site (model chỉ chứa link): 9 nút HS TKBVTC nhận link qua `scripts\dynamo\Link_chung.py` + `gop_link.py` (Chi tiết cửa thêm 2026-11-11: dim bám nét ẩn, template (LINK) ẩn hạng mục). Room trong link có thể sai biên khi link lồng không nạp → công cụ bỏ qua room có cạnh lệch phương tường. Ẩn thiết bị trong link chỉ bằng view filter; template điều khiển filter thì chỉ báo. Người dùng chưa bấm trong Revit của mình.

**Why:** model Site của dự án chỉ chứa link kiến trúc / kết cấu, trước đó các nút không tag, không hatch được gì.

**How to apply:** sửa quy tắc đọc link thì sửa `Link_chung.py` rồi chạy `gop_link.py`, `gop_lomo_shaft.py`, sinh lại nút. Revit không lọc được Schedule theo tầng khi có link, nên bảng là drafting view `lk_bang_ve`. Bấm thử nền dùng `_tmp\hs_site_link\chay.py` (MessageBox phải thay, nếu không phiên nền bị kẹt). Liên quan [[pyrevit-arvtools-revit2027]], [[tag-cua-revit]].
