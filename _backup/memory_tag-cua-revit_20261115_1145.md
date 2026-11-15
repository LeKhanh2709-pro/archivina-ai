---
name: tag-cua-revit
description: "Nút pyRevit 'Định vị + tag cửa' (gộp MB định vị cửa + Tag cửa 2026-11-03, đã build); tag khung 2 ô mã / rộngXcao mm đã duyệt + build; đặt lên sheet + thống kê đã duyệt + build"
metadata:
  node_type: memory
  type: project
  originSessionId: 162e704b-b0d3-405e-9e69-a0b441874c0d
  modified: 2026-11-03T13:52:29.640Z
---

Nút một chạm ARV Tools → HS TKBVTC → **Định vị + tag cửa** (thư mục nút `TagCua`, lõi `scripts\dynamo\TagCua_TuDong.py`, skill `tag-cua-revit`). Người dùng yêu cầu gộp 2 nút MB định vị cửa + Tag cửa (2026-11-03): bấm trên mặt bằng tầng → tạo / mở `MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>` (template tường + sàn Halftone, ẩn nội thất, thiết bị vệ sinh, Mechanical Equipment) rồi tag. Đã build, người dùng chưa bấm thử.

Tag giống mẫu CAD (khung chữ nhật 2 ô: mã / `1400X2195` theo Width, Height mm): người dùng duyệt ảnh + build 2026-11-03. API 2027.3 không tạo / không đổi định dạng nhãn, nên nhãn mm chép từ `lib\tag_cua\ARV_TagNguon_Door / _Window.rfa` (dựng từ family `AV-Tag-Window-Lomo` trong file FPT P4 L1-L2).

Đặt lên bản vẽ (duyệt + build 2026-11-03): bấm nút → hộp thoại `lib\arv_hoi_sheet.py` hỏi giai đoạn / hạng mục / khổ A1–A0 / số hiệu → sheet + 2 bảng thống kê cửa góc phải dưới, tỉ lệ tự chọn trước khi tag. Builder có móc `hoi` trong MOT_CHAM cho nút cần hỏi thêm.

Sửa sau lần chạy trên model thật G19_A_L3-32 (duyệt + build 2026-11-03 chiều): mặt bằng giữa khổ giấy, ưu tiên 1:100, tag xoay theo tường + gọn 14x7 mm chữ 2 mm, loại view riêng MẶT BẰNG ĐỊNH VỊ CỬA (mục Floor Plans riêng), template ẩn Elevation + filter ẩn trục link (Type Name khác loại trục file hiện tại). Chưa thử lại trên model thật.

Lần 3 (tối 2026-11-03, người dùng "có vẻ OK", build): tỉ lệ cố định 1:100; tag gần cửa KHÔNG đè hình (đã thử đặt trên ô cửa, người dùng bỏ); thu trục sát nhà; bảng thống kê sát góc khung. File hộp thoại arv_hoi_sheet.py dùng chung với nút Chi tiết cửa (phiên khác) – không xoá hàm hoi.

Tường / cột / vách (21:00 2026-11-03, duyệt + build): tường xây Halftone không tô, vách BTCT + cột tô đặc xám viền đen bằng filter (ghi đè màu theo hạng mục Walls không hiện trong 2027.3); ẩn Sections. Chưa thử với link KC thật.

**Why:** người dùng dặn "đưa ra ảnh kết quả trước, duyệt rồi mới build" — luôn gửi ảnh thử trước khi build nút.

**How to apply:** khi quay lại, hỏi kết quả bấm nút trong Revit thật (dự án thật nhóm sheet 2 cấp, có thể có khung A0 – G19 mẫu không có). Sửa gì cũng gửi ảnh duyệt trước khi build. Thử như [[revit-2027-dynamo-tu-dong]] và [[pyrevit-arvtools-revit2027]]; không mở file lớn khi Revit người dùng đang chạy ([[khong-lam-phien-may-nguoi-dung]]).
