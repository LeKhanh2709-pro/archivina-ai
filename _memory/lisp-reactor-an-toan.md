---
name: lisp-reactor-an-toan
description: "Reactor AutoLISP an toàn — không sửa CSDL trong commandEnded, không entget trong objectModified; block động tạo bằng -BEDIT/BPARAMETER/BACTION"
metadata:
  node_type: memory
  type: project
  originSessionId: 76f2a5b5-b8aa-4917-aa80-c955d362948c
  modified: 2026-10-29T08:42:36.735Z
---

Rút ra khi làm block động kéo chiều dài cho lệnh VK (2026-10-29), thử bằng `acad.exe /b`:
- Sửa nội dung block (xoá / thêm đối tượng trong bản `*Uxx`) ngay trong callback `:vlr-commandEnded` làm hỏng CSDL: AUDIT dừng giữa pass 1, SAVEAS không ra file. Phải gửi việc sửa ra dòng lệnh bằng `vla-SendCommand "(ham)\n"` (trong script `/b` lệnh gửi này KHÔNG tự chạy → khi thử thì gọi tay hàm).
- `entget` trong callback `:vlr-objectModified` (acdb reactor, tham số `(r (list db ename))`) lúc SAVEAS → AutoCAD lỗi 0xC0000005. Callback chỉ ghi ename; lọc khi hết lệnh; tắt khi `beginSave` → `saveComplete`.
- LISP tạo được tham số động bằng dòng lệnh: `-BEDIT <tên>`, `BPARAMETER _L [_L nhãn] p1 p2 vị-trí-nhãn <số grip>`, `BACTION` chọn tham số bằng ĐIỂM (không nhận ename) → `_T` (Stretch) → điểm → khung → chọn đối tượng (không hỏi vị trí action ở 2027), `BSAVE`, `BCLOSE`. `BACTIONTOOL` không chạy ở dòng lệnh. Đổi giá trị bằng `vla-put-Value` → bản chèn sang `*Uxx`, tên gốc = `EffectiveName`.

**Why:** hai lỗi trên tốn nhiều lượt thử mới tìm ra; áp dụng cho mọi LISP dùng reactor (VK, sau này các lệnh khác).
**How to apply:** khi viết reactor: callback chỉ ghi nhận, sửa bản vẽ ở ngoài reactor; lệnh đọc block vách xét `EffectiveName`. Xem [[vk-mat-dung-dang-do]], [[thu-lisp-nap-nhu-appload]].

Thêm (2026-10-29): AutoLISP KHÔNG phân biệt hoa thường — biến cục bộ `h` đè mất tham số `H` (ô xem trước MDVK co thành 1 chấm). Đặt tên khác hẳn (`rx` / `ry`). Thử hộp thoại DCL thật: phiên ACAD riêng `/b` gọi lệnh, tìm cửa sổ bằng EnumWindows theo PID rồi PrintWindow (`_tmp\vk_bang\chup_cua_so.ps1`); UI Automation quét cả cây hay quá thời gian. Ghép code LISP bằng Python: viết `\t` trong chuỗi, không để lọt ký tự TAB thật (LISP đọc thành dấu cách).
