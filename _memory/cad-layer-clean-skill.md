---
name: cad-layer-clean-skill
description: Skill làm sạch DWG của người dùng ở C:\Users\Khanh\Downloads\cad-layer-clean — cấu hình đã thiết lập và lưu ý khi chạy
metadata:
  node_type: memory
  type: reference
  originSessionId: 887bf5ae-db11-4852-94f7-98e2ddeadbb5
  modified: 2026-10-21T07:37:56.785Z
---

Skill `cad-layer-clean` (không nằm trong danh sách skill, đọc SKILL.md trực tiếp): `C:\Users\Khanh\Downloads\cad-layer-clean`. Chạy bằng AutoCAD 2027 accoreconsole.

- 2026-10-21: đặt LISPSYS = 1 trong registry profile `AutoCAD Architecture (Global)` (R26.0\ACAD-A104:409). Nếu = 0, `(open f "w" "utf8")` lỗi "too many arguments".
- `config/projects/CAD STANDARD_c8112cab/map.csv` khởi tạo 116 dòng từ file 254HQV tầng 4 (người dùng duyệt, kết quả họ xác nhận đúng). `settings.json` cùng thư mục = bộ công tắc 254 HQV (KILL/LAYOUT/PURGEZE tắt, blockContent=map).
- Còn thiếu dòng `LAYER,AV-P-LO MO,A-Wall-Open` (đang rơi vào wildcard `AV-P-*` → 0).
- PURGE All của AutoCAD 2027 tự xoá text rỗng dù PURGEZE tắt → model có thể lệch vài TEXT rỗng; kiểm tra trước khi báo.
- Script .ps1 có tiếng Việt phải lưu UTF-8 có BOM (PowerShell 5.1).
