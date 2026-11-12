---
name: skill-lisp-dung-nhieu-may
description: "Mọi skill / LISP làm ra phải chạy được trên máy khác (không gắn cứng D:\\AI, Program Files, venv) — chốt 2026-10-23"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 17d27e28-4e59-4b38-88bb-3fe287d2a879
  modified: 2026-10-23T06:54:26.562Z
---

Mọi skill và LISP tạo ra từ nay phải dùng được ở các máy khác nhau (người dùng chốt 2026-10-23, CLAUDE.md quy tắc 8).

**Why:** người dùng chép skill / LISP sang nhiều máy công ty; bản cũ gắn cứng `D:\AI\...`, `C:\Program Files\Autodesk\AutoCAD *`, venv nên chạy máy khác bị lỗi.

**How to apply:**
- PowerShell: dot-source `scripts\moi_truong.ps1` (bản giống hệt ở chong-tham-mat-bang, ngan-chay-truc-hkt, truc-lo-mo-mep) → `Get-GocAI`, `Get-ThuMucTam`, `New-ThuMucLam`, `Find-AutoCAD`, `Find-Python`; máy mới chạy `cai_dat_python.ps1`.
- LISP: tự tìm file ngoài (setenv nhớ lại, `ARCHIVINA_*`, Support Path, `%USERPROFILE%\.claude\skills`, `<ổ cứng>:\AI\.claude\skills`, cuối cùng getfiled); `and`/`or` trả về T — lấy chuỗi bằng setq trong cond.
- Đặt tạm rồi trả lại UCS World (cả trước `-WBLOCK`: WBLOCK lấy UCS làm WCS file mới), HPANNOTATIVE 0; UNDO Control None/One thì bỏ nhóm undo; thoát `@ # .` trong tên layer cho `-LAYER`.
- Hatch NET: máy này lấy từ acad.pat (NET 1000 = lưới 125 mm như file mẫu); đo lưới thực rồi chỉnh tỉ lệ, MEASUREMENT không ảnh hưởng.
- Máy khác KHÔNG cài gì (chốt 2026-10-23): LISP cần Python thì kèm gói Python mang theo (Python nhúng + thư viện, chép thư mục), vd. `D:\AI\_tools\CHONGTHAM_python` → `<ổ>:\AI\_tools\` máy kia; CHONGTHAM.lsp nhúng sẵn script (gop_chongtham.ps1).
- Liên quan: [[layer-lo-mo-a-mep]], [[khong-tao-excel]].
