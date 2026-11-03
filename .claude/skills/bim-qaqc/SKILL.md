---
name: bim-qaqc
description: Kiểm tra QA/QC mô hình Revit Kiến trúc/Kết cấu nhà cao tầng theo tiêu chuẩn Archivina (ISO 19650, LOD theo giai đoạn, parameter bắt buộc, level/grid A-S). Dùng khi người dùng muốn kiểm tra, rà soát, QA/QC mô hình hoặc chuẩn bị phát hành/chia sẻ mô hình.
---

# /bim-qaqc – Kiểm tra QA/QC mô hình

Skill này **chỉ đọc**: không sửa mô hình, chỉ báo cáo và đề xuất. Mọi sửa đổi sau đó phải làm qua script riêng, theo quy tắc trong CLAUDE.md gốc (Transaction, dry-run, BIM Manager duyệt).

## Áp dụng tại D:\AI (bổ sung 2026-11-03, ưu tiên hơn phần dưới khi mâu thuẫn)
- Nguồn: bộ `AI REVIT` của đồng nghiệp (commit `b7381e6`); bản gốc giữ nguyên ở `D:\AI\AI REVIT\.claude\skills\bim-qaqc\`.
- Tuân thủ QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md` (không xoá, sao lưu `_backup\`, chống bịa số liệu, ổ khác phải hỏi).
- Đường dẫn: `standards/` → `D:\AI\standards\` (`naming-iso19650.md`, `lod-matrix.md`, `required-parameters.md`); `projects/` → `D:\AI\projects\` (mẫu `_TEMPLATE`); `tools/pyrevit/ARV.extension/…/QAQC.panel/` → `D:\AI\scripts\pyrevit\ARV.extension\ARV.tab\QAQC.panel\` (KHÔNG viết vào `ARVTools.extension`: tab đó sinh tự động bằng `build_from_dynamo.py`).
- Có MCP `revit-archivina` (xem `D:\AI\scripts\mcp\revit-archivina\README.md`) thì đọc trực tiếp Revit đang mở bằng tool đọc (`rv_thong_tin`, `rv_liet_ke`, `rv_chi_tiet`, `rv_canh_bao`, `rv_phong`, `rv_khoi_luong`) thay cho bước sinh script khi phù hợp; vẫn chỉ đọc.
- Báo cáo `.md` mặc định; KHÔNG tạo `.xlsx` nếu người dùng không yêu cầu.

## Bước 1: Xác định phạm vi

Hỏi người dùng nếu chưa rõ:
1. **Mã dự án.** Đọc `projects/<mã>/CLAUDE.md`. Nếu chưa có, đề nghị tạo từ `projects/_TEMPLATE`.
2. **Giai đoạn**: TKCS (LOD 200), TKKT (LOD 300) hoặc TKBVTC (LOD 350).
3. **Bộ môn và file**: A, S hoặc cả hai. Dùng file local hoặc detached, **không dùng file central**.
4. **Mục đích**: kiểm tra định kỳ, trước khi chia sẻ (WIP → SHARED) hay trước khi phát hành (→ PUBLISHED).

## Bước 2: Đọc tiêu chuẩn

- `standards/naming-iso19650.md`
- `standards/lod-matrix.md`
- `standards/required-parameters.md` (nếu file vẫn là placeholder, cảnh báo người dùng và chỉ kiểm tra các mục còn lại)
- Phần khác biệt riêng trong CLAUDE.md của dự án (ưu tiên áp dụng)

## Bước 3: Sinh script kiểm tra pyRevit (read-only)

Viết script vào `tools/pyrevit/ARV.extension/ARV.tab/QAQC.panel/<Tên>.pushbutton/script.py`. Nếu script đã có thì dùng lại. Script **không mở Transaction** và gồm các nhóm kiểm tra:

| # | Hạng mục | Nội dung kiểm tra |
|---|---|---|
| 1 | Tên file | Khớp regex trong `naming-iso19650.md` (nhóm tầng `BS/PD/TY/RF/ZZ`, bộ môn `A/S/C`); mã bộ môn khớp nội dung mô hình |
| 2 | Level | Tên theo `B*/L##/RF/TR`, không trùng cao độ, đúng danh sách của dự án |
| 3 | Grid & Level A↔S | Mô hình A có Copy/Monitor từ S; dung sai 0 mm, mọi lệch cao độ hoặc vị trí đều báo |
| 4 | View & Sheet | Tên theo quy ước; view `WIP_` không được nằm trên sheet; view không dùng |
| 5 | Family | Tên `ARV_*`; family mặc định Autodesk; family in-place |
| 6 | Parameter bắt buộc | Theo `required-parameters.md` và giai đoạn: rỗng, sai định dạng, trùng Mark |
| 7 | Warnings | Tổng số, nhóm theo loại; ưu tiên các loại trùng phần tử, chồng lấn tường/sàn, room không kín |
| 8 | LOD | Kiểm tra mẫu theo `lod-matrix.md`, ví dụ ở TKKT dầm/cột phải có vật liệu |
| 9 | Cao tầng | Group tầng điển hình đồng nhất; FFL − SSL đúng chiều dày hoàn thiện |
| 10 | Sức khoẻ file | Dung lượng, số phần tử, link CAD import (không link), purge được bao nhiêu |

Đơn vị hiển thị là mm, đổi bằng `UnitUtils`. Script xuất kết quả ra CSV UTF-8 có BOM.

## Bước 4: Báo cáo

Tạo báo cáo tiếng Việt `projects/<mã>/qaqc/QAQC_<PRJ>_<Bộ môn>_<YYYYMMDD>.md` (kèm `.xlsx` nếu người dùng cần):

1. **Tóm tắt**: dự án, file, giai đoạn, ngày, kết luận **ĐẠT / KHÔNG ĐẠT** để chuyển trạng thái.
2. **Bảng tổng hợp** theo 10 hạng mục: số lỗi, mức độ (🔴 Nghiêm trọng / 🟡 Cần sửa / ⚪ Lưu ý).
3. **Chi tiết lỗi**: ElementId, category, vị trí (trục-tầng), mô tả, đề xuất sửa.
4. **Việc cần làm**: ai sửa và hạn xử lý (để trống cho BIM Manager phân công).

Tiêu chí KHÔNG ĐẠT khi chuyển SHARED/PUBLISHED: còn lỗi 🔴, sai tên file, lệch level/grid A-S, hoặc thiếu parameter bắt buộc của giai đoạn.

## Bước 5: Kết thúc

- Tóm tắt kết quả cho người dùng trong 3–5 dòng.
- Đề xuất script sửa lỗi tự động cho các lỗi lặp lại (ví dụ đổi tên view hàng loạt). **Không tự chạy**; script sửa phải theo quy trình dry-run và duyệt.
