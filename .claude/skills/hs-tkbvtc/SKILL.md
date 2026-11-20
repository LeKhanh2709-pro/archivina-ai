---
name: hs-tkbvtc
description: 'Bộ công cụ chạy nền cho agent hs-tkbvtc – làm hồ sơ thiết kế bản vẽ thi công (HS TKBVTC) trên BẢN SAO model Revit 2027 chứa link: khảo sát model (mặt bằng, template, khung tên, sheet, giai đoạn / hạng mục, cửa theo tầng), chạy các nút Archivina > HS TKBVTC (Ngăn cháy lan, Định vị + tag cửa, Định vị lan can louver, Chi tiết cửa; Chống thấm cũng chạy được) theo file phương án JSON trong phiên Revit riêng chạy nền, mở file TÁCH khỏi central, kiểm tra từng bản vẽ (số hiệu, tràn vùng vẽ, viewport / bảng đè nhau, tag đè nhau), xuất PNG, lưu ra .rvt mới. Dùng khi người dùng nhờ "làm hồ sơ TKBVTC", "chạy agent HS TKBVTC", "trình bày mặt bằng ngăn cháy / định vị cửa / lan can / chi tiết cửa cho nhiều tầng", hoặc sửa / thử agent hs-tkbvtc.'
---

# Bộ công cụ agent HS TKBVTC

Agent: `.claude\agents\hs-tkbvtc.md` (quy trình làm việc với người dùng). File này mô tả công cụ.
Người dùng chốt 2026-11-15 (trả lời 15 câu hỏi): xem mục "Quy tắc đã chốt" trong file agent.

## Thành phần (không gắn cứng đường dẫn – quy tắc 8)
| File | Việc |
|---|---|
| `scripts\chay_nen.ps1 -Viec <viec.json>` | 1 phiên Revit 2027 riêng, chạy nền (`cua_so_phien.ps1`: dời sang màn hình phụ / ẩn, trả focus). Journal mở `ext\mo_dau.rvt` (dự án trống, chưa có thì tự tạo 1 lần) → nút `Mo` → nút `Chay` → chờ `XONG` trong `<ket_qua>\bao_cao.txt` → đóng phiên. Phiên thoát trước khi bấm nút (bẫy pyRevit lần đầu nạp extension) thì tự chạy lại 1 lần vào `<ket_qua>_lan2`. Cuối: đếm dòng mượn phần tử từ central trong journal (phải = 0). |
| `ext\ARVAgentHS.extension` | Nút thử, chỉ nạp trong lúc chạy (`pyrevit extensions paths add/forget`). `Mo` (IronPython) mở file đích; `Chay` (CPython) chạy `scripts\chay_hs.py`. Đọc `ext\buoc.txt` (đường dẫn file việc). |
| `scripts\chay_hs.py` | Trong Revit: khảo sát / chạy nút theo phương án / kiểm tra bản vẽ / ảnh / lưu. Gọi lại thư viện của nút Hồ sơ đã duyệt (`ARVHoSoDuyet.extension\lib\arv_ho_so_duyet.py`) để trả lời sẵn hộp thoại và chạy `script.py` của từng nút Archivina. |
| `mau\phuong_an_mau.json` | Mẫu phương án (định dạng của nút Hồ sơ đã duyệt + mục `ChiTietCua`, `thong_tin_du_an`). |
| `scripts\ke_hoach.py` | NGOÀI Revit. Kế hoạch 2 cấp + xem trước model theo `khao_sat.json`; `--tao-viec` sinh phương án con, file việc, chuỗi phiên. |
| `scripts\danh_gia.py` | NGOÀI Revit. Soát 1 lần chạy: trạng thái từng bản vẽ, gợi ý xử lý theo loại lỗi, luật chạy lại, `--truoc` so ảnh. |
| `scripts\so_anh.py` | NGOÀI Revit. So 2 ảnh / 2 thư mục lần chạy, khoanh + đánh số vùng khác. |
| `scripts\so_chuan.py` | NGOÀI Revit. Tạo chuẩn từ lần đã duyệt / so lần mới với chuẩn (hồi quy). |
| `scripts\soat_chung.py`, `mau\goi_y_sua.json` | Phần dùng chung: phân loại lỗi, rút số liệu từ dòng báo của lõi; bảng gợi ý theo loại lỗi. |

Máy khác: cần Revit 2027 + pyRevit 6.5.5 + thư mục `<gốc>\scripts\pyrevit\ARVTools.extension` và `ARVHoSoDuyet.extension`
(gốc = cha của `.claude`, hoặc biến `ARCHIVINA_AI`); `ARCHIVINA_REVIT` / `ARCHIVINA_PYREVIT` ép đường dẫn khi tìm không ra.
Chưa thử trên máy khác (`Cần xác nhận lại`).

## File việc (JSON, mỗi lần chạy 1 file, thư mục kết quả MỚI mỗi lần – không ghi đè)
```json
{"che_do": "khao_sat | chay | dat_mark_vk | kiem_tra | script",
 "script": "<file .py chạy trên file đã mở (che_do script, 2026-11-18): có sẵn doc, uiapp, DB, w, KET, KQ, V, luu_ra>",
 "mo": "<.rvt cần mở>",                 "phuong_an": "<phuong_an.json>  (chay)",
 "chi": ["<view>|<nút>", "..."],         "luu": "<.rvt lưu ra – file MỚI>",
 "ket_qua": "<thư mục mới>",             "log": "<thư mục log lõi + đệm CAD, dùng chung cả việc>",
 "anh": true, "tra_loi_xoa": "khong",   "khao_sat_view": ["<mặt bằng cần đếm cửa theo Type Mark>"],
 "nap_lai_link": {"<tên link .rvt>": "<bản sao link trên D:>"},
 "sheet_tien_to": ["A_TC.14."]          (kiem_tra: chỉ kiểm tra + xuất ảnh các tờ có số hiệu bắt đầu như vậy, không chạy nút)}
```
Đường dẫn trong JSON viết bằng `/` (đỡ lỗi thoát `\`). Tên nút: `NganChay`, `TagCua`, `LanCanLouver`, `ChiTietCua`, `ChongTham`.

## Công cụ soát ngoài Revit (2026-11-17, áp dụng ý tưởng của BIMgent; người dùng: "áp dụng … cho agent tkbvtc")
Python có Pillow + numpy (máy này `<gốc>\_tools\venv`), không gắn cứng đường dẫn (tìm theo `__file__`), không ghi đè
(file đã có thì thêm `_2`). Không cần Revit, nên chạy được cả lúc một chuỗi phiên nền đang chạy.
- `ke_hoach.py <phuong_an.json> [--khao-sat <khao_sat.json>]` → `ke_hoach.md/json` cạnh phương án.
  - Cấp cao = các LƯỢT (người dùng chốt 2026-11-19, thay cho "thử 1 tầng → các tầng còn lại"): mỗi lượt trọn 1 nút cho
    mọi tầng → soát → duyệt đúng mới sang lượt sau; thứ tự cố định `LUOT` = Chống thấm → Ngăn cháy lan → Định vị cửa +
    Chi tiết cửa (chung 1 lượt) → Định vị lan can, louver; nút không có trong phương án thì bỏ lượt đó. Các bước gắn nhãn
    [TỰ ĐỘNG] / [CLAUDE SOÁT] / [NGƯỜI DÙNG].
  - Xem trước: chỗ `<…>` / `[Chờ bổ sung]` còn trong phương án; mặt bằng nguồn thiếu; template thiếu hoặc khoá tỉ lệ khác
    yêu cầu; khung tên / giai đoạn / hạng mục chưa có; tờ số hiệu đã có view; tầng ≥ 2 view đích mà thiếu `view_dich`.
    Luật view đích chép theo `arv_ho_so_duyet.view_dich`.
  - Từ chối chạy khi phương án nằm trong thư mục skill.
- `ke_hoach.py … --tao-luot <số lượt | tên 1 nút của lượt> --mo <.rvt> [--nap-lai-link <json>] [--them-viec '<json>']`
  → 1 chuỗi phiên cho cả lượt (mọi tầng; lượt 3: phiên TagCua trước rồi các phiên ChiTietCua, phiên sau mở file phiên
  trước lưu), tên `NN_<Nút>_luot<k>[_n]`. Thử 2026-11-19 trên bản chép `phuong_an_03_day_du.json` của G19 Side: 4 lượt,
  lượt 3 = 1 phiên tag cửa 4 tầng + 6 phiên chi tiết cửa.
- `ke_hoach.py … --tao-viec <Nút> thu|con_lai|tat_ca --mo <.rvt> [--thu-tang <view>] [--nap-lai-link <json>] [--them-viec '<json>']`
  (riêng 1 nút, khi người dùng bảo làm riêng; `tat_ca` = mọi tầng)
  - Chi tiết cửa chia ≤ 7 cửa / mục, ≤ 2 mục / phiên (`--nhom-cua`, `--muc-moi-phien`); nút khác 1 phiên.
  - Ghi `phuong_an_NN_*.json`, `viec\NN_*.json` + `NN_*_lan2.json`, `viec\chuoi_NN_MM.ps1` (phiên không ra file → chạy lại
    đúng 1 lần, vẫn không ra → dừng chuỗi), `viec\khoi_dong_chuoi_NN_MM.ps1` (log vào `lan\`). Số NN tiếp số lớn nhất trong
    `viec\ rvt\ lan\`.
  - Tham số `chay_nen.ps1` truyền bằng hashtable: mảng `@('-ChoToiDa', 9000)` bị PowerShell 5.1 hiểu là giá trị.
- `danh_gia.py <lan> [--truoc <lan trước>] [--ra <thư mục>]` → `danh_gia.md/json`. Mã thoát 0 ĐẠT / 1 còn việc / 2 lỗi chạy.
  - Trạng thái bản vẽ: `ĐẠT` / `CẦN XEM ẢNH` / `CẦN NGƯỜI DÙNG QUYẾT` / `LỖI CHẠY`.
  - Lỗi kiểm tra + dòng `CẦN XEM LẠI` của lõi (kể cả dòng con thụt lề) được phân loại theo `soat_chung.MAU`. Loại tràn tách
    theo cỡ: `tran_nho` ≤ 15 mm, `tran_rat_lon` khung > 1,5 × vùng vẽ, còn lại `tran_vua`. Đè: mặt bằng ↔ bảng = `de_bang`,
    còn lại `de_view`. Mỗi nhóm in nguyên nhân / cách xử lý / ai quyết 1 lần.
  - Câu báo lõi trùng lỗi kiểm tra cùng tờ thì bỏ (kiểm tra là số chắc).
  - Lỗi phiên: Traceback, thiếu `ket_thuc` (phiên dừng giữa chừng), mục lõi lỗi (lấy dòng Exception của mục, vd. AcDbMgd).
    Đếm các lần chạy tới lần này trong cùng thư mục `lan\` có cùng `chi` và cùng loại lỗi; vượt `1 + chay_lai_toi_da` →
    KHÔNG CHẠY LẠI NỮA.
  - Đọc dòng mượn central từ `<lan>_chay_nen.log` nếu có. Cuối file có gợi ý câu hỏi, 1 câu / loại, gom các tờ.
- `so_anh.py A.png B.png [--ra x.png]` hoặc `--thu-muc <lan A> <lan B> --ra <thư mục mới>`.
  - Cắt về khung nội dung, nét lệch ≤ 2 px không tính khác, gom vùng theo lưới 24 px.
  - Ảnh ra: nền B nhạt, nét chỉ có ở A đỏ, chỉ có ở B xanh, khung cam đánh số. Ghép tờ theo số hiệu trong tên PNG.
- `so_chuan.py tao <lan…> --ra <chuan.json> --duyet "<câu duyệt>"` / `so <lan…> --chuan <chuan.json> [--anh]`.
  - Khoá mục = `view|nút` (chi tiết cửa thêm Mark đầu tiên), gộp nhiều phiên. Số nguyên phải bằng, diện tích ±0,05 m².
  - `HỒI QUY` = trước ĐẠT nay KHÔNG ĐẠT / mất tờ / mất mục / lõi lỗi. `LỆCH` = số liệu hoặc loại lỗi đổi. Ảnh khác = cần xem.
    Mã thoát 2 / 1 / 0.
- Thêm loại lỗi mới: 1 dòng regex trong `soat_chung.MAU` + 1 khoá cùng tên trong `mau\goi_y_sua.json`; thêm số liệu:
  1 dòng trong `soat_chung.SO_LIEU`.
- Thử 2026-11-17 trên kết quả cũ (`_tmp\hs_agent_cai_tien\`, chỉ đọc thư mục các việc):
  - danh_gia G19 `00\lan\06` → 3 tờ, đúng 3 lỗi đã thấy trên ảnh; FPT P5 `lan\24` "được chạy lại", `lan\26` trở đi "KHÔNG
    chạy lại nữa"; G19 Side `lan\07` → lỗi AcDbMgd mục Tầng 2 + phiên dừng giữa chừng.
  - so_anh P5 lan 20 / 22 khoanh đúng bảng lan can mới.
  - so_chuan lan 20 với chính nó 0 lệch; chuẩn gộp 6 phiên chi tiết cửa G19 Side khớp.
  - ke_hoach P5 hỏi đúng 2 tờ đã có nội dung; chuỗi thử với `chay_nen` giả chạy lại 1 lần rồi dừng đúng.
  - Chưa chạy trong một việc thật với Revit (`Cần xác nhận lại`).
- Chưa làm: ảnh đánh số tại chỗ lỗi (tag đè / viewport tràn). Cần `chay_hs.py` ghi toạ độ khung lỗi trên tờ;
  không sửa trong lúc chuỗi G19 Side 17 → 19 đang chạy vì mỗi phiên đọc lại file này.

## Hành vi cần biết
- **Tách central**: file workshared mở bằng `DetachAndPreserveWorksets` (mọi workset) → không mượn phần tử từ central thật
  (journal báo 0 dòng mượn). Lưu ra = `SaveAs` central MỚI (bản sao trên `D:`), lần sau mở lại cũng tách.
- **Không mở file bằng API trong CPython**: CPython đã chạy rồi mới mở file thì Revit nạp `AcDbMgd` (tham chiếu
  `DesktopConnectorInterop` 26 không có trên máy) → mọi `clr.AddReference` sau đó lỗi. Vì vậy nút `Mo` là IronPython và
  journal mở trước dự án trống `ext\mo_dau.rvt`.
- Hộp thoại "đặt lên bản vẽ" của nút: trả lời sẵn theo phương án (như nút Hồ sơ đã duyệt). View đích đã nằm trên bản vẽ
  thì giữ template / tỉ lệ đang có.
- Câu hỏi xoá / gộp / vẽ lại của lõi: mặc định trả lời **KHÔNG** và ghi vào `can_hoi` (agent phải hỏi người dùng);
  `tra_loi_xoa: "co"` chỉ khi người dùng đã đồng ý đúng việc đó.
- Chi tiết cửa: chọn sẵn mỗi `mark` 1 đối tượng trên tầng (cửa theo Type Mark, vách kính theo Mark; cửa nằm trong vách
  kính tính theo vách; cả trong link). Không chọn được gì thì không chạy nút (tránh nút chờ chọn trên màn hình).
  `them_in` cũng áp cho mục ChiTietCua (2026-11-18), vd. `{"0": "id;id"}` = làm đúng danh sách id (bỏ qua vùng chọn).
- Chi tiết vách kính bản vẽ RIÊNG (2026-11-18, người dùng: "tách riêng chi tiết cửa và chi tiết vách kính, … theo thứ tự
  và theo tầng"): khoá `ten_vk` (mặc định `CHI TIẾT VÁCH KÍNH`, lõi thêm tên tầng: `CHI TIẾT VÁCH KÍNH TẦNG 1`) và `so_vk`
  (trống = tiếp sau tờ vách kính đã có, chưa có thì bắt đầu từ `so` của cửa) trong mục ChiTietCua; khung tên / giai
  đoạn / hạng mục như cửa. Lõi làm vách kính (theo tầng + Mark) → cửa đi → cửa sổ (theo Type Mark); bỏ cửa Fire Rating,
  cửa thang máy, louver. Mỗi mục 1 lần bấm → nhiều tầng nhiều mục thì tờ vách kính tầng sau nằm sau tờ cửa tầng trước:
  muốn đúng thứ tự cả bộ thì gom vách kính mọi tầng vào 1 mục bằng `them_in {"0": "id;id"}` (id ghép của phần tử link
  như trong báo cáo lõi) hoặc cho `so_vk` dãy riêng. Kiểm tra tờ vách kính bỏ so tên với `ten`.
- Kiểm tra bản vẽ (`kiem_tra` trong `ket_qua.json`, ĐẠT khi `loi` rỗng): số hiệu đúng yêu cầu; mọi viewport / bảng nằm
  trong vùng vẽ khung tên (đo nét dài family khung tên như `DatSheet_chung.sh_vung_ve`, sai số 1 mm); viewport / bảng
  không đè nhau; tag trên mặt bằng không đè nhau (tag có leader ước lượng bằng khung cỡ trung vị của tag cùng kiểu, tâm tại
  đầu tag). Tên bản vẽ khác yêu cầu chỉ là lưu ý. Thêm các dòng `CẦN XEM LẠI` của lõi (`can_xem` từng mục).
- Khoá thêm của từng mục trong phương án (2026-11-15, FPT P5): `view_dich` = tên view đích khi tầng có ≥ 2 view cùng
  loại (công cụ mở thẳng view đó → nút không mở hộp chọn view; thiếu khoá này mà tầng có ≥ 2 view thì mục KHÔNG chạy, ghi
  vào `can_hoi` – hộp chọn view WinForms làm phiên nền đứng mãi); `khong_dung_cad: true` = IN[21] "Không dùng CAD link"
  của Chống thấm / Ngăn cháy (tầng có ≥ 2 CAD link ở các view khác nhau thì lõi dừng); `them_in: {"<số IN>": giá trị}`
  = ô nhập bất kỳ khác của lõi.
- Khoá `tao_view_moi: true` (2026-11-16, người dùng "Tạo view mới, thử"): trước khi bấm nút, view đích có sẵn cùng tầng
  (view mẫu đã có tag / hatch) được ĐỔI TÊN trên bản sao (`MẪU - …`, bỏ chữ khoá) → nút tạo view mới; view mẫu vẫn nằm
  trên bản vẽ cũ, không xoá gì; template mang chữ khoá thì không chạy, ghi `can_hoi`. Dùng kèm số hiệu mới (`-AG`).
  CHƯA chạy được lần nào: 2026-11-16 Revit không mở được P5 (xem dòng dưới).
- Nút `Mo` ghi locale CRT trước khi mở file (`LOCALE truoc … -> C` trong `mo.txt`) và đặt `C`. 2026-11-16 locale đã là
  `C` mà P5 vẫn lỗi `CArchiveException 105` lúc giải nén bảng phần tử (mỗi lần hỏng 1 stream khác: 3970 / 102 / 339 /
  1302), cả bản gốc `00_` lẫn bản Revit tự lưu `04_`; G19 mở bình thường. 15/11 tỉ lệ mở được 2 / 4, 16/11 0 / 4.
  Nguyên nhân chưa rõ (`Cần xác nhận lại`): không phải locale, không phải file hỏng (cùng file lúc được lúc không).
- **Đặt tên vách kính trong file link** (2026-11-16, G19 Side; người dùng: "tên của VK nếu chưa có thì theo thứ tự các
  tầng, ví dụ tầng 1 là VKT1-01, VKT1-02…; các cửa trùng nhau trong dự án thì triển khai 1 lần"):
  - Vách kính thường nằm trong file link (chỉ đọc) → chép file link về `rvt\`, chạy `che_do: "dat_mark_vk"` trên bản sao
    đó (`vk_tang` [số tầng], `vk_dang` "VKT{t}-{n:02d}", `vk_bo_loai` ["tuong lam"] = kiểu curtain wall không phải vách
    kính, `luu` = file link mới).
  - Vách chưa có Mark được đặt theo thứ tự đọc (trên → dưới dải 3 m, trái → phải). Vách giống hệt nhau (kiểu, dài, cao,
    panel / cửa cùng vị trí, lật đầu vẫn tính) dùng chung 1 Mark; giống vách đã có Mark thì lấy Mark đó. Ghi `vk_mark.json`.
  - File việc của model chính: khoá `nap_lai_link` {"<tên link .rvt>": "<file link mới>"}. Nút `Mo` (IronPython) nạp lại link
    bằng `RevitLinkType.LoadFrom` sau khi mở; kết quả ghi trong `mo.txt`.
  - Thử G19 Side: Tầng 1 13 vách → VKT1-01…10 + 1 vách lấy T1-VK.04.2; tag 16 / 16 vách bằng Mark.
  - Mark mới chỉ nằm trên BẢN SAO link: muốn dùng thật thì người dùng đặt Mark trong file link thật (`Cần xác nhận lại`).
  - **Bản chép link cũ dần** (G19 Side 2026-11-20: chép 16/11, KTS sửa tiếp trên ổ A: tới 20/11 → tầng 1 chống thấm lệch 30 – 45 mm
    so với link người dùng thấy, vách kính đổi dài, số VKT dịch 1 số). Trước mỗi lượt dùng bản chép: so `LastWriteTime` bản ổ A:
    với bản chép (đọc ổ A: phải hỏi người dùng, quy tắc 7); mới hơn thì xin chép lại → `dat_mark_vk` lại → chạy. Dấu hiệu nhận ra
    trên ảnh người dùng: nét kết cấu (link nạp thẳng ổ A:) trùng, nét kiến trúc lệch.
  - Soát đường bo chống thấm (và vùng hatch khác bám tường) bằng NÉT REVIT VẼ, không bằng toạ độ tính lại: script
    `_tmp\hs_agent\02_G19_Side\viec\xuat_dxf_chong_tham.py` (che_do script: DXF view gộp link) + `soi_dxf_chong_tham.py`
    (ngoài Revit: A-WALL / S-COLS = mặt thô, A-WALL-FNSH = trát / ốp; OK / LẤN / HỤT / TRỐNG mỗi 25 mm, ảnh từng phòng) +
    `ghep_truoc_sau.py`.
- Chi tiết cửa chạy chậm trên model nhiều link (G19 Side 242 link instance: ~3 phút / cửa, vách kính 5 – 8 phút, càng về
  sau càng chậm vì mỗi lần tạo view Revit cập nhật đồ hoạ mọi section đã tạo). Bài học 2026-11-16 (lần `lan\07` chạy 3 giờ,
  17 tờ, mất hết vì chưa lưu):
  - Chia `mark` thành nhóm ~7 / mục và chạy THÀNH CHUỖI PHIÊN, mỗi phiên 1 – 2 mục, mở file của phiên trước, `luu` file mới
    (mẫu `_tmp\hs_agent\02_G19_Side\viec\tao_chuoi_08_15.py` → `chuoi_08_15.ps1`; lõi xếp tiếp vào tờ cũ cùng `so`).
  - Trong 1 phiên, sau vài mục chi tiết cửa Revit có thể nạp `AcDbMgd` → mục sau lỗi `DesktopConnectorInterop 26`
    ngay ở `clr.AddReference` (giống bẫy mở file trong CPython) → thêm lý do để mỗi phiên ít mục.
  - Revit có lúc dựng đồ hoạ > 15 phút không ghi journal. `chay_nen.ps1 -JournalDung <phút>` (mặc định 15) và từ
    2026-11-16 CPU của Revit còn tăng thì vẫn tính là tiến triển. Chuỗi dùng `-ChoToiDa 9000 -KhongTienTrien 120 -JournalDung 30`.
  - **MỌI phiên của chuỗi phải có `nap_lai_link`** khi model dùng link bản sao (G19 Side chiều 16/11: phiên 08 mở file do
    phiên có LoadFrom lưu ra thì link `04_*_mark_VK.rvt` nạp được, nhưng file phiên 08 lưu ra (chỉ nạp link lúc mở) thì các
    phiên 09 – 14 mở lên KHÔNG nạp link này (journal không hề thử nạp; link ổ A: vẫn nạp) → "chọn 0 đối tượng", 3 phiên
    không làm gì; ảnh tờ Tầng 1 chỉ còn khung rỗng cho tới khi link nạp lại. Phiên 15 có `nap_lai_link` → `LinkLoaded`,
    0 link không nạp. Nguyên nhân gốc `Cần xác nhận lại`). Chuỗi chạy lại: `viec\tao_chuoi_16_18.py`.
  - Ảnh / `kiem_tra` của từng phiên chỉ có tờ phiên đó chạm tới, và tờ được xuất ngay sau MỤC ĐẦU (thiếu cửa mục sau xếp
    thêm vào tờ đó) → cuối chuỗi chạy 1 phiên `che_do: "kiem_tra"` + `sheet_tien_to` trên file cuối (mẫu
    `viec\19_kiem_tra_toan_bo.json`) để có ảnh + kiểm tra của mọi tờ.
  - **Chuỗi dài phải chạy trong tiến trình RIÊNG** (`Start-Process powershell -WindowStyle Hidden -File <khởi động>.ps1`,
    mẫu `viec\khoi_dong_chuoi_17_19.ps1`): chuỗi chạy nền bằng tool Bash của Claude bị tắt theo khi phiên Claude kết thúc
    (G19 Side 16/11 17:34, mất phiên 15 đang chạy); tiến trình riêng sống qua lúc phiên kết thúc (chạy tiếp 17:38 – 21:19
    không ai trông). Task Scheduler (`Register-ScheduledTask`) bị chặn quyền – không dùng. Log do `powershell.exe` 5.1 ghi
    bằng `*>` là UTF-16 → trong Bash đọc bằng `iconv -f UTF-16LE -t UTF-8`, `grep` thẳng không thấy gì. Viết file `.ps1`
    bằng tool Write, không qua heredoc Python / Bash (`\\v` thành ký tự điều khiển, file khởi động 17/11 hỏng đường dẫn).
    Máy khởi động lại giữa chừng thì phiên đang chạy mất (17/11 08:15, phiên 17), chuỗi nối lại từ file rvt mới nhất.
  - Kết quả G19 Side (16 – 17/11): 56 chi tiết (43 cửa + 13 vách kính) trên 20 tờ A_TC.14.xx, 4 tờ định vị cửa, ~13 giờ
    máy chạy; vách kính 7 cái / phiên mất 1,5 – 2,2 giờ. Bàn giao `_tmp\hs_agent\02_G19_Side\ban_giao\`.
- Khảo sát / chọn cửa KHÔNG gom phần tử theo view (`FilteredElementCollector(doc, viewId)` bắt Revit dựng đồ hoạ từng
  view; FPT P5 37 link treo > 15 phút, 23 GB RAM) – link thấy trong view xét bằng `IsHidden`.
- Thông tin dự án (`thong_tin_du_an`): điền tham số chữ của Project Information theo đúng tên; tên không có thì báo.
- Nút Hồ sơ đã duyệt hiện CHƯA chạy mục `ChiTietCua` (bỏ qua) và chưa điền `thong_tin_du_an`.

## Đã thử (2026-11-15, bản sao G19, `_tmp\hs_agent\00_thu_G19\`)
- Khảo sát 30 mặt bằng / 25 template / 4 khung tên / 30 sheet, cửa theo Type Mark Tầng 1 (~40 giây / phiên).
- Chạy Ngăn cháy lan + Định vị + tag cửa + Chi tiết cửa (DG16, 32) Tầng 1 → A.4-101 / A.7-110 / A.7-120, lưu
  `rvt\06_chay_thu.rvt`; kiểm tra báo đúng 3 lỗi thấy trên ảnh (trục A chạm dải khung tên; mặt bằng định vị cửa văng khỏi
  tờ vì template `1.2` của G19 làm viewport 1250 × 2038 mm; ký hiệu mặt cắt chạm khung trên).
- Chưa thử trên model chỉ chứa link (HQV Site) và file workshared (`Cần xác nhận lại`).
