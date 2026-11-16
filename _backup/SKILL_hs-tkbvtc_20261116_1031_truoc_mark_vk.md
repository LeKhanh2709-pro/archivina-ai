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

Máy khác: cần Revit 2027 + pyRevit 6.5.5 + thư mục `<gốc>\scripts\pyrevit\ARVTools.extension` và `ARVHoSoDuyet.extension`
(gốc = cha của `.claude`, hoặc biến `ARCHIVINA_AI`); `ARCHIVINA_REVIT` / `ARCHIVINA_PYREVIT` ép đường dẫn khi tìm không ra.
Chưa thử trên máy khác (`Cần xác nhận lại`).

## File việc (JSON, mỗi lần chạy 1 file, thư mục kết quả MỚI mỗi lần – không ghi đè)
```json
{"che_do": "khao_sat | chay",
 "mo": "<.rvt cần mở>",                 "phuong_an": "<phuong_an.json>  (chay)",
 "chi": ["<view>|<nút>", "..."],         "luu": "<.rvt lưu ra – file MỚI>",
 "ket_qua": "<thư mục mới>",             "log": "<thư mục log lõi + đệm CAD, dùng chung cả việc>",
 "anh": true, "tra_loi_xoa": "khong",   "khao_sat_view": ["<mặt bằng cần đếm cửa theo Type Mark>"]}
```
Đường dẫn trong JSON viết bằng `/` (đỡ lỗi thoát `\`). Tên nút: `NganChay`, `TagCua`, `LanCanLouver`, `ChiTietCua`, `ChongTham`.

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
