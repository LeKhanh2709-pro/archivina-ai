---
name: khong-tu-tao-view-template
description: Nút Revit HS TKBVTC không tự tạo / sửa view template; hộp thoại hỏi View template + Tỉ lệ (tỉ lệ theo template)
metadata:
  node_type: memory
  type: feedback
  originSessionId: c255fec8-f33d-4348-a02f-a65b90ce83fa
  modified: 2026-11-05T07:22:45.775Z
---

Nút pyRevit tạo mặt bằng (Chống thấm, Ngăn cháy lan, Định vị + tag cửa, Định vị lan can louver, Tường xây) KHÔNG tự tạo hay sửa view template. Hộp thoại sau khi bấm nút hỏi thêm **View template** (template mặt bằng có sẵn hoặc "Không dùng") và **Tỉ lệ**. Chọn template thì tỉ lệ lấy theo template đó; template khoá tỉ lệ thì ô tỉ lệ bị khoá, không gỡ quyền điều khiển tỉ lệ của template (người dùng chốt 2026-11-05).

**Why:** người dùng muốn tự chọn template của công ty thay vì để công cụ sinh template "MẶT BẰNG ..." và filter ARV_* lẫn vào dự án.

**How to apply:** nút mới tạo view cũng làm theo cách này: dùng `_bang(tpl_view=...)` trong `arv_hoi_sheet.py` + `sh_ap_tpl_tl` (DatSheet_chung.py), không gọi CreateViewTemplate / SetNonControlledTemplateParameterIds. Liên quan [[trinh-bay-ban-ve-chong-tham-chay-lan]], [[tag-cua-revit]], [[dinh-vi-lan-can-louver]], [[tuong-xay-revit]].
