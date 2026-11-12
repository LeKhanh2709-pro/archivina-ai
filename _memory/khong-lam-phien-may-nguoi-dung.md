---
name: khong-lam-phien-may-nguoi-dung
description: "Khi thử trên máy người dùng đang làm việc: không mở cửa sổ chiếm bàn phím, không chụp toàn màn hình"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a96cfae0-8a6d-40b8-84de-db94615dcf9f
  modified: 2026-11-10T09:48:23.378Z
---

Không chạy phiên thử có hộp thoại lên màn hình khi người dùng có thể đang làm việc, và không chụp toàn màn hình.

**Why:** Thử hộp thoại WPF 2026-10-31: hộp thoại của phiên thử chiếm bàn phím, chữ người dùng đang gõ trong ứng dụng khác lọt vào ô nhập của phiên thử; ảnh chụp toàn màn hình lọt cả cửa sổ chat riêng tư.

Người dùng chốt thành quy tắc 9 trong CLAUDE.md (2026-11-10): Claude chạy phần mềm luôn ở chế độ nền, không chạy trực tiếp trên màn hình.

**How to apply:** Ưu tiên cách không có cửa sổ: dựng WPF ngoài màn hình rồi chụp PNG, `acad.exe /b` thu nhỏ với hàm giả thay hộp thoại. Cần chụp thì chụp đúng cửa sổ phiên thử bằng `PrintWindow`. Bắt buộc phải mở hộp thoại thật thì báo người dùng trước.
