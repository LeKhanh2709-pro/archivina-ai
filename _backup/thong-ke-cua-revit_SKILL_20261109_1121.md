---
name: thong-ke-cua-revit
description: 'Thống kê + đổi tên cửa Revit – Đứng ở mặt bằng tầng đang mở, bấm 1 nút hiện BẢNG các loại cửa đi / cửa sổ trong mặt bằng (cửa trùng hiện 1 lần): Loại, Cửa (Family : Type), Tên hiện tại, Tên đổi (gõ được), Chiều dài, Chiều cao, SL mặt bằng, SL cả dự án; bấm Đổi tên → đổi Type Mark (tag cửa tự hiện tên mới), báo tên trùng. Tuỳ chọn tạo bảng thống kê (Schedule) Revit cửa đi và cửa sổ của mặt bằng đó: cột Ký hiệu (Type Mark) / Rộng / Cao / Số lượng, gộp theo Type Mark nên cửa trùng ký hiệu chỉ hiện 1 dòng kèm số lượng, dòng TỔNG cuối bảng; lọc theo tầng của mặt bằng, bỏ đối tượng có Type Comments chứa chữ Louver; bấm lại thì cập nhật bảng cũ, không tạo trùng, không xoá. Báo cửa chưa có Type Mark, cùng ký hiệu khác kích thước, mặt bằng crop không thấy hết cửa của tầng. Nút pyRevit Archivina > HS TKBVTC > Thống kê cửa + graph Dynamo ThongKeCua_TuDong.dyn. Dùng khi người dùng nhờ "điền / đổi tên cửa", "đặt lại ký hiệu cửa", "thống kê cửa", "bảng thống kê cửa đi / cửa sổ của tầng", "đếm cửa theo ký hiệu", "schedule cửa gộp trùng", hoặc sửa / thử nút Thống kê cửa.'
---

# Thống kê cửa Revit (Archivina)

Người dùng yêu cầu 2026-11-04: "tạo 1 bảng thống kê các cửa có trong mặt bằng đó, những cửa trùng thì hiện 1 lần", làm
nút riêng (không gắn vào nút Định vị + tag cửa, vốn chỉ tạo bảng khi đặt lên bản vẽ).
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit của người dùng.

## Cách dùng
- Mở mặt bằng tầng → `Archivina` → `HS TKBVTC` → **Thống kê cửa** → hiện **bảng cửa** (`lib\arv_bang_cua.py`, người dùng
  yêu cầu 2026-11-04 tối: "1 bảng hiện ra, có các cửa, tên hiện tại, tên đổi, chiều dài, chiều cao"):
  - mỗi loại cửa (ElementType) thấy trong mặt bằng 1 dòng, bỏ loại có Type Comments chứa chữ Louver; cửa đi trước, cửa
    sổ sau, theo tên;
  - cột: Loại / Cửa (Family : Type) / Tên hiện tại (Type Mark) / **Tên đổi** (gõ, trống = giữ) / Chiều dài / Chiều cao
    (instance trước, type sau; nhiều giá trị thì `800 / 900`) / SL mặt bằng / SL cả dự án;
  - dòng vàng: chưa có tên hoặc cùng tên với loại cửa khác trong bảng;
  - bấm **Đổi tên**: tên mới trùng loại cửa khác cùng hạng mục (cả dự án) hoặc 2 dòng cùng tên mới → hỏi Yes / No;
  - ô "Tạo / cập nhật bảng thống kê Revit" (nhớ lựa chọn ở `%APPDATA%\pyRevit\ARVTools\ThongKeCua.json`, lần đầu tắt).
  - Đổi tên = đổi **Type Mark** của type → áp cho MỌI cửa cùng type trong dự án; tag cửa tự hiện tên mới. Ctrl+Z một lần
    là hoàn tác (transaction `ARV - Thống kê cửa`). View đang mở không phải mặt bằng tầng thì nút nhắc.
- Shift+bấm: hộp thoại 9 ô, mặc định Dry-run (chỉ báo cáo).

| IN | Ý nghĩa | Mặc định |
|---|---|---|
| 0 | Tên view mặt bằng (trống = view đang mở) | trống |
| 1 | Hạng mục: `Cửa đi;Cửa sổ` (bỏ bớt nếu chỉ cần 1 bảng) | `Cửa đi;Cửa sổ` |
| 2 | Type Comments CÓ CHỨA chữ này thì không thống kê (`;` ngăn cách) | `Louver` |
| 3 | Dry-run | True (nút một chạm truyền False) |
| 4 | Mẫu tên bảng (`{loai}`, `{tang}`, `{view}`) | `THỐNG KÊ {loai} - {tang}` |
| 5 | Mở bảng vừa tạo | True |
| 6 | Chỉ đếm cửa thấy trên sheet đặt bảng (Filter by sheet) | False |
| 7 | Đổi tên: JSON `{"<id type>": "<Type Mark mới>"}` (nút điền từ bảng cửa) | trống |
| 8 | Tạo / cập nhật bảng thống kê Revit | True (nút lấy theo ô trong bảng cửa) |

## Quy tắc
1. **Mỗi hạng mục 1 bảng**: `THỐNG KÊ CỬA ĐI - <TẦNG>`, `THỐNG KÊ CỬA SỔ - <TẦNG>`. Revit 2027.3 KHÔNG gộp được cửa đi + cửa
   sổ vào 1 bảng (khảo sát 2026-11-04): bảng nhiều hạng mục không có trường Rộng / Cao (DOOR_ / WINDOW_ / FAMILY_WIDTH đều
   thiếu), bộ lọc chỉ "và" không có "hoặc"; lọc Category chỉ nhận `ElementId` hạng mục, không nhận chuỗi "Doors".
2. **Gộp trùng**: Itemize every instance TẮT, sort / group duy nhất theo Type Mark → mỗi ký hiệu 1 dòng, cột Số lượng
   (Count, hiện tổng) + dòng tổng `TỔNG`.
3. **Cột bảng Revit**: Tên (Type Mark) / Chiều dài / Chiều cao / Số lượng; Rộng / Cao lấy `DOOR_WIDTH` / `WINDOW_WIDTH` (không có thì
   `FAMILY_WIDTH_PARAM`), tương tự chiều cao. Trường khác của bảng nhân bản thì ẩn, không xoá.
4. **Lọc**: Level = tầng của mặt bằng (`FAMILY_LEVEL_PARAM`), Type Comments **không chứa** từng chữ IN[2] (người dùng yêu
   cầu 2026-11-09: "trong type comment của cửa có louver thì không hiện thống kê"; bản cũ chỉ bỏ khi ghi đúng y `Louver`).
   Không phân biệt hoa thường / dấu: `Louver`, `LOUVER nhôm`, `Cửa đi + louver` đều bị bỏ. Bảng Revit dùng
   `ScheduleFilterType.NotContains`; lõi + bảng đổi tên (`arv_bang_cua._loai_tru`) so chuỗi không dấu.
5. **Bảng cùng tên đã có** → cập nhật lại cột / lọc / gộp (không tạo trùng, không xoá). Chưa có → nhân bản bảng cùng hạng
   mục có sẵn của dự án (ưu tiên tên có "thống kê", giữ kiểu trình bày công ty), không có thì tạo mới. Bảng cùng tên khác
   hạng mục thì báo, không đụng.
6. **Filter by sheet TẮT mặc định**: bật thì bảng đặt trên sheet KHÔNG có mặt bằng sẽ trống trơn (đã gặp khi thử).
   Mặt bằng crop 1 phần tầng (vd. `CAN-04 - MB TƯỜNG XÂY`: 9 / 119 cửa đi) thì bảng vẫn đếm cả tầng → công cụ báo
   CẦN XEM LẠI; muốn chỉ đếm cửa của mặt bằng đó: Shift+bấm bật IN[6] và đặt bảng lên sheet có mặt bằng đó.
7. **Báo CẦN XEM LẠI**: cửa chưa có Type Mark (gộp chung 1 dòng trống), cùng Type Mark mà khác kích thước (Revit để trống
   ô Rộng / Cao), cửa thấy trong mặt bằng nhưng Level khác tầng (bảng không đếm), số cửa của tầng ≠ số thấy trong mặt bằng.
8. Mỗi bảng làm trong `SubTransaction`: bảng lỗi giữa chừng thì huỷ riêng bảng đó.
9. "Blank row before data" của Revit (khoảng trống giữa tiêu đề cột và dữ liệu) API không tắt được → bỏ tay trong
   Appearance nếu cần.

10. **Đổi tên làm TRƯỚC bảng thống kê** (cùng transaction) để bảng hiện tên mới. Type Mark chỉ đọc thì báo, không đổi.
    Tên mới trùng type khác vẫn đổi (người dùng đã xác nhận) và ghi CẦN XEM LẠI.

## File
- Bảng cửa: `scripts\pyrevit\ARVTools.extension\lib\arv_bang_cua.py` (viết tay, `hoi_thong_ke_cua(doc, view)` → {7, 8}),
  khai báo `"hoi"` + `"tip"` (tooltip riêng) trong `MOT_CHAM` của builder.
- Lõi: `scripts\dynamo\ThongKeCua_TuDong.py` (+ `.json` spec, `.dyn` sinh bằng `scripts\dynamo\build_dyn.py`).
- Nút: `scripts\pyrevit\ARVTools.extension\Archivina.tab\HoSo.panel\ThongKeCua.pushbutton\` SINH bằng
  `scripts\pyrevit\build_from_dynamo.py "<file mau revit>\dynamo" --chi ThongKeCua` (đặt `PYTHONIOENCODING=utf-8`);
  không sửa tay. Khai báo trong `BUTTONS` + `MOT_CHAM` (`view_in` 0, `tu_khoa` rỗng = mặt bằng tầng đang mở).
- Icon: mdi `table-large` → `scripts\pyrevit\icons\ThongKeCua(.dark).png` (sinh bằng `_tmp\arvtools_icon_thongke\`).

## Cách thử (đã làm 2026-11-04)
- Dynamo trên bản sao `G19_A_L3-32` (`_tmp\revit_thongkecua\thu1..3\`, chạy `_tmp\revit_g19\chay_dynamo_ui.ps1`; journal
  phải ghi UTF-8 KHÔNG BOM, có BOM thì Revit không chạy lệnh và script chờ hết giờ): TẦNG 3 → cửa đi 119 cái / 12 ký hiệu,
  cửa sổ 50 cái / 9 ký hiệu (bỏ 17 Louver), lần 2 cập nhật không trùng. Ảnh bảng: schedule không xuất ảnh trực tiếp →
  đặt lên sheet tạm trong bản sao rồi `ExportImage` (`thu3\anh - Sheet - ZZ-THU - ...png`).
- Nút thật: extension thử `_tmp\pyrevit_thongke\ext\ARVTestTK.extension` (nút `TK` chạy nguyên `script.py` của nút 2 lần),
  `pyrevit extensions paths add` → `_tmp\pyrevit_test\chay_test.ps1 -Journal _tmp\pyrevit_thongke\journal.txt -BaoCao
  _tmp\pyrevit_thongke\kq\ket_qua.txt` → `paths forget`. Kết quả: tạo 2 bảng, mở bảng cửa đi, lần 2 không trùng.

- Bản bảng đổi tên (2026-11-04 21:15): nút thử `TK` đặt `ARV_HOI_ANH` (vẽ bảng ra PNG, coi như bấm Đổi tên) +
  `ARV_TK_THU` (điền sẵn tên đổi) + `arv_bang_cua._LUU` về `_tmp\pyrevit_thongke\kq2\`: "80" → D1 (16 cửa),
  "VKD03-F2E" → D2 (37 cửa), bảng Revit hiện D1 / D2, lần 2 không đổi thêm; ảnh `kq2\bang_lan1.png`, `bang_lan2.png`.

## Trạng thái
Người dùng chưa bấm thử trong Revit của mình, chưa duyệt (`Cần xác nhận lại`). Revit phải Reload pyRevit mới thấy nút.
