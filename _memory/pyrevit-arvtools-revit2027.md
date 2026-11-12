---
name: pyrevit-arvtools-revit2027
description: pyRevit 6.5.5 trên Revit 2027 + extension ARVTools (22 nút từ Dynamo ARV_*); cách chạy thử bằng journal vì pyrevit run hỏng
metadata:
  node_type: memory
  type: project
  originSessionId: 1934bfca-461b-438f-bb4a-fa3f3b7aabf0
  modified: 2026-11-05T02:18:47.079Z
---

Người dùng yêu cầu (2026-10-27) chuyển bộ Dynamo ARV_* sang pyRevit, "thiếu gì thì cứ cài". Kết quả: `D:\AI\scripts\pyrevit\ARVTools.extension` (tab ARV Tools), sinh bằng `build_from_dynamo.py` (core.py = nguyên văn .py Dynamo, inputs.json từ Input node .dyn), thư viện `lib\arv_dynamo_host.py` giả IN/DocumentManager/TransactionManager + hộp thoại WinForms. Nút Chống thấm (panel Hồ sơ) do phiên "Archivina AI repository setup" thêm — không ghi đè.

**Why:** pyRevit 6.4 lỗi CPython trên Revit 2027 ('3.12.3' not in a correct format) → đã nâng 6.5.5 (bản cho user; 7.0 admin từng crash). `pyrevit run` không dùng được trên 2027.

**How to apply:**
- Thử nút: `_tmp\pyrevit_test\chay_test.ps1` mở Revit 2027 bằng journal + RibbonEvent gọi nút thử ASCII `ARVTest` (thêm search path khi thử, gỡ sau). Journal không gọi được panel có tên tiếng Việt có dấu. Xem thêm [[revit-2027-dynamo-tu-dong]].
- CPython pyRevit: `List[T](pylist)` lỗi → thư viện đã thay List; code mới tự viết thì tạo List rỗng rồi Add.
- pythonnet 3.0.3: tên được `from Autodesk.Revit.DB import <tên>` ĐẦU TIÊN trong phiên bị loại khỏi `import *` về sau (kiểm chứng 2026-10-27) → script nút dùng `import Autodesk.Revit.DB as DB`; core dùng `import *` thì bổ sung bằng `dir()`.
- Cách thử nhanh khi ARVTest không được nạp: đặt tạm `<tên>.extension` ASCII vào `D:\AI\scripts\pyrevit` (đã nằm trong search path), xong chuyển về `_tmp` (đã làm ở `_tmp\pyrevit_chongtham\motcham\`).
- Nút Chống thấm là "một chạm" (người dùng chốt 2026-10-27): bấm là vẽ luôn, Shift+bấm là hộp thoại; người dùng tự tạo view chống thấm + đặt sheet.
- Đã thử dry-run G19: 22/22 không lỗi vỏ; 13 nút đọc CAD chưa thử được (G19 không có CAD link); chưa thử ghi thật.
- 2026-10-28 thử trên `file mau revit\G19 CAD.rvt` (có link G19.dwg, file DWG gốc không có trên máy): 24 nút dry-run + 19 nút ghi trên bản sao; khung thử `_tmp\pyrevit_cad\` (nút ASCII ARVCad điều khiển bằng `lenh.json`: survey / run / verify, log ép về `_tmp` bằng USERPROFILE). Cửa đi / Cửa sổ đặt vào tường ốp 10 mm bị Revit xoá → đã sửa (tường < 30 mm không làm tường chủ, nhận ô đã có cửa trên mọi tường theo điểm chèn hoặc tâm hộp bao), dựng lại đủ, không lỗi. Còn mở: Tường từ CAD mất 3/9. Sửa .py file mẫu thì đồng bộ mã vào .dyn bằng `_tmp\pyrevit_cad\dong_bo_dyn.py` (chỉ thay khi khớp bản cũ). Kết quả chi tiết trong README.
- 2026-11-03 người dùng yêu cầu gọn tab: panel Hồ sơ hiện tên **HS TKBVTC** (nút lớn), các panel dựng từ CAD xếp chồng 2–3 nút nhỏ (`STACKS` trong builder). Icon nút: mdi trắng đen như K-TOOL, nguồn `scripts\pyrevit\icons\` (đen + `.dark.png` trắng). Người dùng muốn **xem ảnh xem trước rồi mới build** khi đổi giao diện nút.
- 2026-11-04 người dùng yêu cầu: tab đổi tên **Archivina** (thư mục `Archivina.tab`, extension vẫn `ARVTools.extension`), BỎ panel MEP (4 nút, chuyển vào `_backup\MEP.panel_20261104_1140\`) → 40 nút. Đừng thêm lại nút MEP nếu chưa được yêu cầu.
- 2026-11-05 (người dùng duyệt ảnh): 5 nhóm dựng hình gộp thành panel **Dựng mô hình** gồm 5 nút xổ xuống (`PULLDOWNS` / `GOP_PANEL` trong builder). Xem [[anh-duyet-truoc-khi-build]].
- Liên quan [[bo-dynamo-arv-file-mau]], [[k-tool-tab-ribbon]], [[skill-lisp-dung-nhieu-may]].
