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
  - mỗi loại cửa (ElementType) thấy trong mặt bằng 1 dòng, bỏ loại có Type Comments chứa chữ Louver / Lam thép / Lam nhôm; cửa đi trước, cửa
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
| 2 | Type Comments CÓ CHỨA chữ này thì không thống kê (`;` ngăn cách) | `Louver;Lam thép;Lam nhôm` |
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
   Thêm `Lam thép` (người dùng yêu cầu 2026-11-09, model HQV ghi "CỬA LAM THÉP LOGIA CĂN HỘ") và `Lam nhôm` (người dùng
   yêu cầu cùng ngày); chữ `lam` đứng một mình KHÔNG loại (vd. `Cửa lam gỗ` vẫn thống kê). Bộ lọc bảng Revit phân biệt
   hoa / thường và **mỗi bảng tối đa 8 bộ lọc** (quá thì Revit báo "filter count would be greater than 8", KHÔNG tạo được
   bảng) nên `lap_bang` bỏ chữ cái đầu của từ khoá (`am thép`, `ouver`) và chỉ thêm dạng thường + HOA: 3 từ khoá = 6 bộ lọc
   + 1 lọc tầng, còn dư 1; thêm từ khoá thứ 4 phải đổi cách. Dạng khác (`Lam Thép`) bảng Revit chưa bỏ. Sửa danh sách thì sửa cả `_LOAI_TRU` trong `arv_bang_cua.py` (viết không dấu) và `MAC_DINH` + `.json`.
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

- Từ khoá Lam thép + bộ lọc 3 dạng hoa / thường (2026-11-09, `_tmp\revit_thongkecua\thu6\`, Dynamo trên bản sao L3-32 TẦNG 3, gán thử
  Type Comments): `CỬA LAM THÉP ...`, `cửa lam thép`, `Cửa Lam thép`, `LOUVER nhôm`, `louver` đều bị bỏ ở cả bảng đổi tên và
  bảng Revit (cửa đi 110, cửa sổ 18), `Cửa lam nhôm` vẫn còn. Bản sao HQV 05/11 chưa có loại lam thép nên không dùng để thử.
- Thêm Lam nhôm (2026-11-09, `thu7\` lỗi quá 8 bộ lọc → sửa → `thu8\`, cùng cách thử, chạy `core.py` của nút): `Cửa lam nhôm`,
  `CỬA LAM NHÔM LOGIA`, `lam nhôm sơn tĩnh điện` + các dạng lam thép / louver đều bị bỏ ở cả 2 bảng (cửa đi 112, cửa sổ 19);
  `Cửa lam gỗ`, `Cửa nhôm kính`, `Cửa thép` vẫn còn.

## Cửa sổ "Vách kính" (2026-11-13)
Người dùng yêu cầu: "1 cửa sổ đặt tên cửa đi cửa sổ, 1 cửa sổ tag vách kính bằng mark"; duyệt ảnh bản thử rồi mới build.
- Hộp thoại nút có 2 tab: **Cửa đi, cửa sổ** (như trên) và **Vách kính**. Bấm nút ở tab nào thì làm việc của tab đó
  (tab cửa: bảng thống kê Revit; tab vách: tag); tên đã gõ ở tab kia vẫn được đặt. Tab mở lần trước được nhớ.
- Tab Vách kính (`lay_dong_vk`): curtain wall (`WallType.Kind == Curtain`) thấy trong mặt bằng, kể cả trong file link đúng
  tầng (dòng link chỉ đọc); cùng kiểu + cùng dài + cùng cao + cùng Mark = 1 dòng. Cột: Loại / Vách kính (kiểu tường) / Tên
  hiện tại (Mark) / Tên đổi / Chiều dài / Chiều cao (Unconnected Height) / SL mặt bằng / Đã tag (n / m). Dòng vàng: chưa có
  Mark hoặc trùng Mark với dòng khác.
- **Tên vách = MARK của từng vách** (model HQV: `T1-VK.02`, có tiền tố tầng) → chỉ đặt cho vách của mặt bằng đang mở,
  không có ô "cả dự án". Mark mới trùng vách khác thì hỏi Yes / No.
- **Tag** (`vk_tag` trong lõi, IN[10]): mỗi vách 1 tag TƯỜNG hiện Mark, không leader, nằm theo phương vách (vách dọc → tag
  đứng), giữa vách, phía ngoài nhà, cách mép vách 1 mm giấy. Phía ngoài = phía có nhiều tia dò (0°, ±30°, xa 25 m) không
  chạm tường khác; bằng nhau thì phía không có room; vẫn không rõ thì theo `Orientation` của tường. Tránh tag / chữ đang
  có, tim tường khác (kèm nửa bề dày), khung bao cửa đi / cửa sổ (cả cánh mở): dịch dọc vách (0,5 → 0,12 / 0,88 chiều dài),
  hết chỗ thì đẩy ra xa dần 6 nấc (vượt cung mở cửa), phía ngoài trước rồi phía trong; vẫn vướng thì để chỗ đầu và báo.
  Không tránh đường trục / nét mặt cắt. Vách đã có tag tường trong view: không tag thêm. Vách chưa có Mark: không tag, liệt kê.
  Hạng mục Wall Tags tắt trong view / template thì báo.
- **Family tag** `ARV_Tag Vach Kinh Mark` (kiểu `Mark`), đóng gói ở `lib\tag_vach_kinh\`: dựng từ family
  `AV-Railing Tag- Mark-lan can` của người dùng bằng cách đổi hạng mục family sang Wall Tags qua API
  (`OwnerFamily.FamilyCategory`), nhãn Mark giữ nguyên (API không tạo được nhãn). Dự án chưa có thì lõi tự nạp. Ô "Family
  tag" trong bảng liệt kê thêm các kiểu tag tường của dự án (IN[11]); model HQV L1-L3 không có family tag tường nào.

- **Không tạo bảng thống kê Revit cho vách kính** (người dùng chốt 2026-11-13: "Không cần"); ô bảng thống kê Revit chỉ
  dành cho cửa đi / cửa sổ.

| IN | Ý nghĩa | Mặc định |
|---|---|---|
| 9 | Đặt tên vách kính: JSON `[{"ids": [id vách], "moi": "<Mark>"}]` | trống |
| 10 | Tag vách kính bằng Mark | False (nút lấy theo ô trong bảng, lần đầu bật) |
| 11 | Kiểu tag `Family : Type` (trống = `ARV_Tag Vach Kinh Mark`) | trống |
| 12 | Thư mục family tag đóng gói (trống = `<extension>\lib\tag_vach_kinh`) | trống |
| 13 | Vẫn thống kê cửa đi / cửa sổ nằm trong vách kính (2026-11-14, xem mục dưới) | False |

Cách thử (`_tmp\tk_vach_kinh\`, bản sao `rvt\L1-L3.rvt` chép từ ổ A: `2.HQV_A_ThapB_L1-L3.rvt` do người dùng đưa): nút thử
`ARVTestHS` (`hs_site_link\buoc.txt` → `chay_that.py`, exec `script.py` của NÚT THẬT 2 lần trên view nhân bản có crop) +
`pyrevit_test\chay_test.ps1 -Journal tk_vach_kinh\journal.txt`. Biến thử: `ARV_HOI_ANH` (PNG tab cửa + `_vk.png` tab vách),
`ARV_HOI_TAB` = 1, `ARV_VK_THU` = `{"@trong": "T1-VK.THU%d"}` (điền tên cho dòng chưa có Mark). Kết quả Tầng 1: 53 vách (47
có Mark, 6 chưa), đặt 5 dòng tên thử, tag 53 / 53 chữ đúng Mark, bấm lại không tag thêm; ảnh `kq_that\`. Phiên thử không
đặt `locale` mà Revit không văng. Chưa thử: vách kính trong file link, vách cong, mặt bằng xoay.

## Cửa nằm trong vách kính: không liệt kê, không thống kê (2026-11-14) – QUY TẮC HIỆN HÀNH
Người dùng chốt 2026-11-14: "không tag các cửa, và thống kê các cửa (cửa đi, cửa sổ) khi nằm trong vách kính" (áp cho cả
nút Định vị + tag cửa, xem skill `tag-cua-revit`). Cách hiểu của Claude: cửa đi / cửa sổ có `Host` là curtain wall
(`vk_trong_vach`) thuộc về vách kính – vách có tên riêng theo Mark – nên không đứng riêng trong bảng.
- Hộp thoại (`arv_bang_cua.lay_dong`): không liệt kê loại cửa chỉ nằm trong vách kính, SL mặt bằng / SL đã có không đếm
  các cửa đó; dòng mô tả ghi "Không liệt kê n cửa đi / cửa sổ nằm trong vách kính…".
- Lõi: `dem_trong_view(..., bo_vk)` / `dem_theo_tang(..., bo_vk)` bỏ các cửa đó, báo "bỏ n cái nằm trong vách kính".
  **IN[13]** (bool, mặc định TẮT) = vẫn thống kê cửa nằm trong vách kính như cũ (ô đặt nghĩa ngược vì ô bool trống của
  nút truyền False).
- Bảng thống kê Revit KHÔNG lọc được theo vách chủ → tầng có cửa nằm trong vách kính (hoặc có cửa trong link) thì bảng =
  **bảng vẽ rời** (drafting view, `vk_bang_ve` gọi `lk_bang_ve`), chỉ đếm cửa THẤY trong mặt bằng. Bảng Revit cùng tên có
  từ trước: không xoá, lõi báo CẦN XEM LẠI. Bảng vẽ cũ khác số dòng: HỎI Yes / No rồi mới xoá chữ + nét cũ và vẽ lại
  (giữ góc phải dưới + chỗ nhãn viewport trên bản vẽ); biến môi trường `ARV_VE_LAI_BANG` = 1 / 0 trả lời sẵn khi thử nền.
- Phần vách kính của lõi nay là **khối chung** `scripts\dynamo\VachKinh_chung.py`, chép vào `ThongKeCua_TuDong.py` +
  `TagCua_TuDong.py` bằng `gop_vach_kinh.py` (không sửa tay giữa 2 mốc `PHẦN CHUNG VÁCH KÍNH`); `VK_IN_THU_MUC` = chỉ số ô
  thư mục family tag (12 ở đây).
- Thử nền nút thật (`_tmp\tk_vach_kinh\chay_2nut.py`, nút thử riêng `ARVTestVK` + `chay_nen.ps1`; journal
  `journal_site_dvc.txt` / `journal_l13.txt`):
  - bản sao Site HQV đã có mặt bằng định vị cửa Tầng 1 (cửa trong link): cửa đi 55 cái / 11 ký hiệu, bỏ 39 cái nằm trong
    vách kính, bảng vẽ `THỐNG KÊ CỬA ĐI - TẦNG 1`; bấm lại chỉ cập nhật chữ (`kq_2nut_site\`);
  - bản sao `2.HQV_A_ThapB_L1-L3.rvt` Tầng 1 (cửa trong model chính): 50 cái / 14 ký hiệu, bỏ 25, bảng vẽ thay bảng
    Revit; bấm lại không đổi (`kq_2nut_l13\`).
- Bản trước: `_backup\*_20261114_0910_truoc_bo_cua_vk*`, `_backup\*_20261114_0922_truoc_vach_kinh_chung*`,
  `_backup\*_20261114_1327_truoc_sua_canh_bao*`.

## Trạng thái
Người dùng duyệt ảnh bản thử cửa sổ Vách kính 2026-11-13. Bản 2026-11-14 (bỏ cửa nằm trong vách kính) nút sinh lại 13:28,
`.dyn` sinh lại nhưng chưa chạy thử trong Dynamo; người dùng chưa bấm trong Revit của mình (`Cần xác nhận lại`). Revit
phải Reload pyRevit mới thấy bản mới.
