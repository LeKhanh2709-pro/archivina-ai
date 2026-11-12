---
name: dinh-vi-lan-can-louver
description: "Nút Định vị lan can, louver + Thống kê lan can, louver (2026-11-05): tag + đặt tên theo Mark LK / LV; luôn nạp family; nút thật thử OK trên bản sao L3-32, người dùng chưa bấm bản sửa"
metadata:
  node_type: memory
  type: project
  originSessionId: 3700e046-5b61-4986-b8fb-2b3ee4c31f3a
  modified: 2026-11-05T03:38:10.450Z
---

Người dùng yêu cầu 2026-11-05 skill "mặt bằng định vị lan can, louver", nhận diện + hiện tên theo **Mark**, "giống nút
định vị và tag cửa". Lõi `scripts\dynamo\LanCanLouver_TuDong.py`, skill `dinh-vi-lan-can-louver-revit`. Người dùng
"Duyệt, icon PA1" (mdi tag-text-outline) → đã build nút.

Người dùng đã tự đặt mẫu trong G19 Tầng 1: lan can Mark `LK-01` tag `AV-Railing Tag- Mark-lan can` (có leader), louver
Mark `LV-01` tag `TAG LOUVER MARK`; cả 2 tag nằm ngang, phía ngoài nhà → công cụ theo mẫu này. Chỉ tag Mark đúng tiền tố,
còn lại liệt kê.

Cùng ngày người dùng bấm trên model thật G19_A_L3-32 (10:13, tag 0): báo "chưa load được family" và "thống kê như cửa"
→ luôn nạp family (đóng gói đúng tên G19) + nút mới **Thống kê lan can, louver** (`ThongKeLanCan_TuDong.py`,
`lib\arv_bang_lan_can.py`, icon PA1 table-edit, đã duyệt ảnh + build). Model thật có 17 lan can chưa Mark, 17 louver Mark
số (75…98) → phải đặt tên bằng nút Thống kê trước rồi mới tag được.

**Why:** người dùng muốn bộ hồ sơ định vị giống mặt bằng định vị cửa ([[tag-cua-revit]]), đặt tên như [[thong-ke-cua-revit]].

**How to apply:** khi quay lại, hỏi kết quả bấm nút thật (Reload pyRevit). Chưa rõ: người dùng có chấp nhận cảnh báo
duplicate Mark (0 → 8 trên bản sao) không; có muốn tag lan can luôn có leader như mẫu không (hiện: chỉ khi lệch). Sửa
giao diện thì gửi ảnh trước ([[anh-duyet-truoc-khi-build]]); thử nhánh nạp family phải dùng model không có family; thử như
[[revit-2027-dynamo-tu-dong]] và [[pyrevit-arvtools-revit2027]].
