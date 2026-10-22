# ngan-chay-truc-hkt — Mặt bằng ngăn cháy lan trục / hộp kỹ thuật

Tự động tìm **trục kỹ thuật, hộp kỹ thuật** trên mặt bằng tầng AutoCAD, vẽ **đường bo + hatch ngăn cháy lan**, gom vào block và làm mờ bản vẽ để mặt bằng chỉ nổi phần ngăn cháy.

Gồm 2 cách dùng, cùng một bộ quy tắc:

| Cách dùng | File | Khi nào dùng |
|---|---|---|
| Lệnh AutoLISP `NCL` | `lisp/fire_stop_shaft.lsp` | Người dùng tự chạy trong AutoCAD. Đọc được cả xref đang attach. |
| Skill Claude Code | `SKILL.md`, `scripts/`, `references/` | Claude chạy ngầm bằng AutoCAD Core Console trên bản sao, xuất Excel + ảnh kiểm tra. |

## Lệnh LISP `NCL`

1. Sao lưu bản vẽ (lệnh vẽ thêm vào bản vẽ đang mở).
2. `APPLOAD` → chọn `lisp/fire_stop_shaft.lsp`.
3. Gõ **`NCL`** → lệnh tự làm hết. (`KT-NGANCHAY`: hỏi `[Ve/Danhsach/Thoat]` trước khi vẽ.)
4. Sai thì **Ctrl+Z một lần** để hoàn tác toàn bộ.

Lệnh làm gì:

- **Nhận diện** (quét cả block lồng nhau, xref đã bind, xref đang attach đã nạp — chỉ đọc, **không bind**):
  - dấu X của trục / hộp (2 nét chéo nối góc ô chữ nhật; nhận cả "X lệch" vẽ không chuẩn);
  - ký hiệu ống đứng (block `*pipe*`: ống tròn + cùm U) — khung lỗ mở MEP (`*LO MO*`) có ống bên trong là hộp kỹ thuật dù không vẽ X;
  - block lỗ mở sàn `lo mo` không có ống → bỏ;
  - bỏ qua cabin thang máy, đồ nội thất, nét khuất tầng hầm, vùng đã có hatch ngăn cháy.
- **Vẽ** mỗi vùng: polyline kín màu 6 + hatch `NET` tỉ lệ 1000, góc 315°, True Color RGB 220,30,30, liên kết với polyline — cả hai trên layer **`A-Material`**.
- **Gom** toàn bộ đường bo + hatch vừa vẽ vào block `NGAN CHAY LAN` (trùng tên thì `NGAN CHAY LAN 2`…), chèn tại 0,0 trong Model.
- **Làm mờ** (chỉ trong bảng layer, không sửa đối tượng): tắt layer nội thất / thiết bị vệ sinh, đổi các layer khác sang True Color 150,150,150; **giữ nguyên màu layer của xref khung tên**. Trạng thái layer cũ lưu thành layer state `TRUOC NGAN CHAY LAN`.
- Bản vẽ đang mở ở layout: lệnh tự sang Model để vẽ rồi trả về layout cũ.

Tên block / layer khác dự án: sửa danh sách trong hàm `nc:cfg` ở đầu file LISP.

Yêu cầu: AutoCAD 2025 / 2026 (đã chạy thử trên Core Console 2027), `LISPSYS = 1`, file LISP lưu UTF-8.

Giới hạn: mặt bằng có trục nhà song song X, Y; đường bo lấy theo ô X / khung lỗ mở (có chỗ hụt vài cm so với lòng tường); đối tượng gán màu riêng (không BYLAYER) giữ nguyên màu; xref chưa nạp được (không tìm thấy file) thì lệnh cảnh báo và bỏ qua.

## Skill Claude Code

Chép cả thư mục vào `.claude/skills/ngan-chay-truc-hkt/` của dự án. Quy trình và quy tắc chi tiết: `SKILL.md`, `references/nhan-dien.md`.

- `scripts/dwg_to_dxf.ps1` — DWG → DXF trên bản sao (Core Console).
- `scripts/tim_truc_ky_thuat.py` — dò trục / hộp từ DXF, xuất JSON + Excel + PNG (cần `ezdxf`, `shapely`, `openpyxl`, `matplotlib`).
- `scripts/ve_hatch_vao_ban_sao.ps1` — vẽ vào bản sao DWG, gom block, làm mờ layer (dùng chung hàm của file LISP).

Bản vẽ có xref đang attach: DXF không chứa nội dung xref → dùng lệnh `NCL`.
