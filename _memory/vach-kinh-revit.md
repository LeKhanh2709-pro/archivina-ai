---
name: vach-kinh-revit
description: "Nút pyRevit Vách kính (curtain wall theo quy tắc VK/MDVK) — đã làm 2026-11-01, đã thử trên bản sao, người dùng chưa bấm thử"
metadata:
  node_type: memory
  type: project
  originSessionId: 2afbcbac-3181-417f-a64f-c91e05a90d02
  modified: 2026-11-01T06:38:24.648Z
---

Người dùng yêu cầu 2026-11-01: tự vẽ vách kính trên Revit theo quy tắc lệnh VK / MDVK ([[vk-mat-dung-dang-do]]). Đã làm nút `ARV Tools → Vách kính` (IronPython) + skill `.claude\skills\vach-kinh-revit` (quy tắc, file, cách thử ghi đủ ở đó).

Người dùng chốt: đố 65x150; L mép ngoài - mép ngoài; pick 2 điểm dựng curtain wall mới; bảng nhập tên / dài / cao vách / rộng + cao cửa sổ, cửa đi (rộng TÂM - TÂM, cao từ sàn); tên trống tự đặt; cửa đi Door-Curtain-Wall-Double-Glass, cửa sổ CuaSoVK_A_loai2 giống hệt MDVK; đổi chiều dài tự chia lại; không dim / view mặt đứng / lam nhôm; góc vuông "như mẫu" (đố góc 150x150 + kính góc), ô tích "vách góc vuông" trong bảng, góc pick = mép ngoài, đố góc thay đố biên, mỗi cánh chia < 1200, cánh có tab riêng, tên tự nhập, chỉ góc 90°.

Tự quyết (chưa hỏi, `Cần xác nhận lại`): dùng kiểu đố mới `ARV_Đố 65x150` đặt giữa kính (đố nổi lệch 45,5); vách thẳng pick trên trục kính; cánh 2 ô 1 không đặt cửa; vách có cả cửa đi + cửa sổ đặt cả 2 đố ngang.

**Why:** tiếp tục việc dở cần biết điều đã chốt và điều còn mở.
**How to apply:** đọc SKILL.md trước khi sửa; hỏi lại các điểm tự quyết khi người dùng phản hồi sau bấm thử.
