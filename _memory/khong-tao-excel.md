---
name: khong-tao-excel
description: Không tự tạo file Excel kèm kết quả bản vẽ; chỉ xuất khi người dùng yêu cầu
metadata:
  node_type: memory
  type: feedback
  originSessionId: a672e335-b6af-4609-8e94-6faf49c726a9
  modified: 2026-10-23T02:24:28.222Z
---

Không tạo file Excel (.xlsx) kèm kết quả nếu người dùng chưa yêu cầu. Kết quả mặc định chỉ gồm bản sao DWG + ảnh PNG duyệt.

**Why:** Người dùng nói ngày 2026-10-23, sau lần chạy thử chống thấm CT1: "K CẦN TẠO FILE EXCEL NHÉ, CẦN THÌ T SẼ YÊU CẦU".

**How to apply:** Skill chong-tham-mat-bang đã đổi thành chỉ xuất Excel khi có cờ `--excel` (cả lệnh LISP `CHONGTHAM`). Với skill khác (ngan-chay-truc-hkt, truc-lo-mo-mep, dien-tich-ch) đang xuất Excel mặc định: khi chạy thì không xuất Excel / không báo link Excel. Không tự sửa code các skill đó nếu chưa hỏi. Liên quan [[chi-lam-1-ban-ve]].
