---
name: k-tool-tab-ribbon
description: "Tab ribbon K-TOOL = K-TOOL.dll (C#, .NET 10, LISP nhúng sẵn) + K-TOOL.lsp, sinh bằng scripts\\ktool\\build.ps1; Claude đã tự thử 6 nút chạy được 2026-10-29"
metadata:
  node_type: memory
  type: project
  originSessionId: 2e103871-ab92-46ca-a609-4b5fcf6ce815
  modified: 2026-10-30T06:49:28.011Z
---

Người dùng muốn (2026-10-29) các lệnh LISP đã làm hiện thành **tab K-TOOL trên ribbon** (cạnh tab ATool) và "gắn LISP vào nút". Hiện tại: `K-TOOL.dll` (AdWindows, 5 file LISP là EmbeddedResource; bấm nút → load file → `(c:<lệnh>)`, ghi `K-TOOL.log`) + `K-TOOL.lsp` (chỉ NETLOAD DLL).

**Why:** bản toolbar COM không hiện; bản nút gọi `kt:chay` qua K-TOOL.lsp bấm không ra. AutoCAD 2027 chạy **.NET 10**.

**How to apply:**
- Sửa `scripts\ktool\K-TOOL_nguon.lsp` / `KToolApp.cs` hoặc file LISP nhúng → chạy `build.ps1`; không sửa tay file trong `scripts\lisp`. DLL đang nạp bị khoá → AutoCAD phải mở lại.
- Tự thử được: mở phiên ACA riêng trên bản sao trong `_tmp\k_tool_test2\` (`/product ACA /b run.scr` để NETLOAD), bấm nút bằng UIA InvokePattern (`invoke.ps1`), đọc lịch sử dòng lệnh bằng UIA (`cuoi.ps1`), chụp màn hình ảo (`chup.ps1`, AutoCAD ở màn hình phụ X âm). Chỉ đóng phiên mình mở.
- Icon nút: người dùng chỉ muốn **trắng đen** kiểu Material (chốt 2026-10-30, chê ô màu + chữ và bản vẽ tay có ô màu) → path bộ mdi nhúng trong `BieuTuong.cs`, icon trắng nền trong suốt; bộ đã duyệt: view-column-outline / window-closed-variant / close-box-outline (lỗ mở = ô vuông có X) / wall-fire / water-check. Đổi icon thì dựng bảng ứng viên đánh số cho người dùng chọn, chép path bằng script (gõ tay dễ sai số).
- Máy người dùng: `TRUSTEDPATHS` trống → hộp bảo mật khi nạp từng LISP; `LISPSYS = 0` → Lomo / NCL / CHONGTHAM in lỗi font. Xem [[skill-lisp-dung-nhieu-may]].
