---
name: hatch-1-doi-tuong
description: "Chống thấm / ngăn cháy lan Revit: mọi vùng của 1 view vào MỘT Filled Region (không tách mỗi WC / trục), để kiểm soát diện tích"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f85604ab-af36-4f22-b24a-8284d8cc26a5
  modified: 2026-11-12T06:05:19.719Z
---

Hatch chống thấm và ngăn cháy lan trên Revit: mọi vùng của một view phải nằm trong MỘT Filled Region nhiều vòng. Không tạo mỗi WC / mỗi trục một Filled Region (người dùng chốt 2026-11-12).

**Why:** Người dùng muốn bấm vào là thấy ngay tổng diện tích. Hàng chục hatch rời thì không kiểm soát được.

**How to apply:**
- Vẽ mới bằng `sh_ve_hatch_gop` (khối chung `DatSheet_chung.py`).
- API không sửa được sketch Filled Region. Muốn thêm vùng vào hatch cũ thì phải tạo vùng gộp mới rồi xoá vùng cũ, và chỉ xoá sau khi người dùng đồng ý trong hộp thoại (quy tắc 1).
- Vòng chồng / chạm nhau thì hợp bằng Boolean. Trước đó nắn các đỉnh lệch nhau dưới 1 mm.
- Áp cùng nguyên tắc cho công cụ hatch Revit mới. Liên quan [[trinh-bay-ban-ve-chong-tham-chay-lan]], [[bo-sat-tuong-tho]].
