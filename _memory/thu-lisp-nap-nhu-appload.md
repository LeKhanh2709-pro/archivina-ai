---
name: thu-lisp-nap-nhu-appload
description: "Khi chạy thử LISP bằng acad.exe /b (dán nội dung vào .scr), phải bọc file trong (progn ...) để lỗi nạp lộ ra giống APPLOAD"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 76f2a5b5-b8aa-4917-aa80-c955d362948c
  modified: 2026-10-29T03:27:19.454Z
---

Chạy thử LISP bằng cách dán nội dung vào .scr thì mỗi biểu thức chạy riêng; một dòng lỗi bị bỏ qua và các dòng sau vẫn chạy. APPLOAD thì dừng ngay ở dòng lỗi. Ngày 2026-10-29, dữ liệu nhúng của VKMD.lsp có một danh sách thiếu dấu `'`. Bản thử vẫn OK, nhưng trên máy người dùng cửa đi và ký hiệu kính không vẽ ra; người dùng phải báo lỗi.

**Why:** người dùng mất một lần thử và phải tự phát hiện lỗi.
**How to apply:** trong script thử, bọc nội dung file LISP trong `(progn ... (setq <cờ> T))` rồi ghi log cờ đó cùng các biến dữ liệu nhúng. Dữ liệu sinh tự động thì mọi danh sách phải có `'`. Áp dụng cho [[vk-mat-dung-dang-do]] và các LISP một file khác (VK, Lomo, CHONGTHAM).
