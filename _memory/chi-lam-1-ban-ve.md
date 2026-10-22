---
name: chi-lam-1-ban-ve
description: "Khi sửa quy tắc skill bản vẽ, chỉ làm lại đúng 1 bản vẽ đang trao đổi, không tự làm lại các bản vẽ khác"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d14d2079-f997-4da6-afc7-5462c04a7f29
  modified: 2026-10-22T03:43:56.236Z
---

Mỗi lần người dùng nêu quy tắc mới hoặc sửa lỗi (vd. skill [[ngan-chay-truc-hkt]]), chỉ xuất lại **một** bản vẽ: bản đang được trao đổi. Không tự chạy lại song song các bản vẽ khác (vd. đã làm cả tầng 4 Tháp B lẫn CT1 khi chỉ cần CT1).

**Why:** Người dùng nhắc 2026-10-22 sau khi Claude tạo 2 bản v4 cùng lúc: "lần sau chỉ cần làm 1 bản vẽ thôi, k cần làm 2 bản". Mỗi lần chạy một file DWG 50 MB mất 10–20 phút, và nhiều bản làm rối thư mục kết quả.

Người dùng xác nhận: "t giao cho t làm file ct1 thì b chỉ cần làm file đó thôi, k cần sửa file cũ, khi nào cần t sẽ yêu cầu".

**How to apply:** Cập nhật script / quy tắc cho mọi bản vẽ, nhưng chỉ vẽ lại file được giao. Không sửa hay làm lại các file đã làm trước đó (bản vẽ khác hoặc kết quả cũ), cũng không hỏi có làm lại không: người dùng sẽ tự yêu cầu khi cần.
