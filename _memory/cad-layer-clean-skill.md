---
name: cad-layer-clean-skill
description: Skill làm sạch DWG của người dùng ở C:\Users\Khanh\Downloads\cad-layer-clean — cấu hình đã thiết lập và lưu ý khi chạy
metadata:
  node_type: memory
  type: reference
  originSessionId: 887bf5ae-db11-4852-94f7-98e2ddeadbb5
  modified: 2026-10-23T09:28:10.481Z
---

Skill `cad-layer-clean` (không nằm trong danh sách skill, đọc SKILL.md trực tiếp): `C:\Users\Khanh\Downloads\cad-layer-clean`. Chạy bằng AutoCAD 2027 accoreconsole.

- 2026-10-21: đặt LISPSYS = 1 trong registry profile `AutoCAD Architecture (Global)` (R26.0\ACAD-A104:409). Nếu = 0, `(open f "w" "utf8")` lỗi "too many arguments".
- 2026-10-23: người dùng thấy AutoCAD "lạ", yêu cầu khôi phục → đã trả LISPSYS về 0 và LogFilePath về `C:\Users\Khanh\AppData\Local\Autodesk\ACA 2027\enu\` (script thử nghiệm từng `setvar LOGFILEPATH` vào `_tmp` mà không trả lại). Bản registry trước khi khôi phục: `D:\AI\_backup\AutoCAD2027_registry_20261023_1604.reg`. Không tự đặt lại LISPSYS = 1 hay đổi biến lưu registry nào nếu chưa hỏi người dùng; script chạy acad.exe phải trả lại mọi biến lưu registry đã đổi.
- 2026-10-23: Ctrl+C bắt chọn lại đối tượng do QAFLAGS = 1 (FixedProfile\General Configuration, dùng chung cho acad.exe và Core Console; bit 1 làm ^C trong macro huỷ vùng chọn). Người dùng đặt lại 0. Không tìm thấy nguồn trong D:\AI hay cad-layer-clean (đã quét cả chuỗi UTF-16 trong dll) → nguồn `Cần xác nhận lại`. Script không được setvar QAFLAGS; nếu cần cho EXPLODE thì trả lại 0 ngay.
- `config/projects/CAD STANDARD_c8112cab/map.csv` khởi tạo 116 dòng từ file 254HQV tầng 4 (người dùng duyệt, kết quả họ xác nhận đúng). `settings.json` cùng thư mục = bộ công tắc 254 HQV (KILL/LAYOUT/PURGEZE tắt, blockContent=map).
- Còn thiếu dòng `LAYER,AV-P-LO MO,A-Wall-Open` (đang rơi vào wildcard `AV-P-*` → 0).
- PURGE All của AutoCAD 2027 tự xoá text rỗng dù PURGEZE tắt → model có thể lệch vài TEXT rỗng; kiểm tra trước khi báo.
- Script .ps1 có tiếng Việt phải lưu UTF-8 có BOM (PowerShell 5.1).
