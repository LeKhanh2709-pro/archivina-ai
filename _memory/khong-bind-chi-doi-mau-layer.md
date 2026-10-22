---
name: khong-bind-chi-doi-mau-layer
description: Script AutoCAD không được tự bind xref/block/link và không sửa màu từng đối tượng; muốn làm mờ thì chỉ đổi màu trong bảng layer
metadata:
  node_type: memory
  type: feedback
  originSessionId: d14d2079-f997-4da6-afc7-5462c04a7f29
  modified: 2026-10-22T04:33:27.978Z
---

Khi script / LISP cần làm mờ hay đổi màu bản vẽ (vd. mặt bằng ngăn cháy lan của [[ngan-chay-truc-hkt]]): **chỉ đổi màu (và bật/tắt) trong bảng layer**. Không entmod màu từng đối tượng, không bind xref, block hay link (XBIND/BIND, đổi xref thành block…).

**Why:** Người dùng nhắc 2026-10-22: "không tự ý bind file. chỉ được phép ép màu về xám, còn các block, các link, xref k được tự ý bind, hãy chỉ ép màu trong bảng layer". Trước đó Claude đã ép màu 16.954 đối tượng trong block và đề xuất bind xref tường PCCC.

**How to apply:** Đối tượng gán màu riêng (không BYLAYER) hoặc nằm trong xref ngoài thì để nguyên màu, chỉ báo cho người dùng biết. Muốn bind hay sửa đối tượng thì phải được người dùng yêu cầu rõ.
