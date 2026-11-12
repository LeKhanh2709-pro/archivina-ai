---
name: layer-lo-mo-a-mep
description: "Lỗ mở MEP (block A-MEP, block gom LO MO MEP) luôn đặt trên layer \"A-MEP\" (gạch ngang), tuân thủ tuyệt đối; lệnh LISP là LOMO trong Lomo.lsp"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6cad50f4-64f2-48b7-a28a-965e7fe0e6f3
  modified: 2026-10-22T13:24:05.112Z
---

Mọi đối tượng lỗ mở (block A-MEP, block gom `LO MO MEP`) LUÔN đặt trên layer `A-MEP` (gạch ngang), không dùng `A_MEP` (gạch dưới) dù block mẫu `FILE MẪU LỖ MỞ.dwg` đặt trên `A_MEP`. Người dùng yêu cầu "tuân thủ tuyệt đối" (22/10/2026). LISP của skill `truc-lo-mo-mep` tên `Lomo.lsp`, lệnh `LOMO` (người dùng đặt). Người dùng muốn thao tác đơn giản nhất: `Lomo.lsp` là MỘT file gộp sẵn (APPLOAD 1 file), tạo bằng `gop_lomo.ps1`, không bắt người dùng nạp thêm file khác.

**Why:** người dùng chốt quy ước layer lỗ mở cho cả hồ sơ, bản đầu đặt theo block mẫu (`A_MEP`) là sai ý.

**How to apply:** khi viết / sửa script lỗ mở hoặc bất kỳ việc gì tạo đối tượng lỗ mở MEP, dùng layer `A-MEP`; chỉ lấy màu / nét của `A_MEP` mẫu khi phải tạo mới layer. Không đổi tên file / lệnh LOMO. Liên quan [[chi-lam-1-ban-ve]].
