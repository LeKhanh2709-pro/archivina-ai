---
name: dinh-vi-lan-can-louver-revit
description: 'Mặt bằng định vị lan can, louver Revit – Đứng ở mặt bằng tầng bấm 1 nút: tạo / mở "MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER - <tầng>" (template riêng như mặt bằng định vị cửa: tường xây Halftone, vách / cột BTCT tô đặc, ẩn nội thất, thiết bị vệ sinh, trục link), rồi tag lan can (Railings) và louver (Windows / Generic Models) theo MARK: Mark tiền tố LK = lan can, LV = louver, tag hiện đúng Mark; tag ưu tiên ngay giữa đối tượng, phía ngoài nhà, không đè tường / cửa / chữ, lệch thì có leader; bấm lại không trùng; Mark trống / sai tiền tố thì liệt kê; tuỳ chọn đặt lên bản vẽ kèm bảng thống kê lan can / louver. Nút pyRevit Archivina > HS TKBVTC > Định vị lan can, louver + graph Dynamo LanCanLouver_TuDong.dyn. Kèm nút Thống kê lan can, louver: bảng đặt tên (Mark) + schedule như nút Thống kê cửa. Dùng khi người dùng nhờ "mặt bằng định vị lan can", "định vị louver", "tag lan can / louver theo mark", "tag LK / LV", "thống kê lan can / louver", "đặt Mark lan can", hoặc sửa / thử các nút này.'
---

# Mặt bằng định vị lan can, louver (Archivina, Revit 2027)

Người dùng yêu cầu 2026-11-05: "TẠO SKILL MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER. Lan can louver thì dựa vào mark để nhận diện
tên, yêu cầu giống với nút định vị và tag cửa" (ảnh G19 Tầng 1, khoanh tag mẫu ở mặt trái nhà).
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit người dùng.

## Mẫu người dùng (G19 Tầng 1, đọc bằng MCP + khảo sát bản sao 2026-11-05)
- Lan can `Railing : Glass Panel - Bottom Fill` 1051218, Mark `LK-01`, tag family `AV-Railing Tag- Mark-lan can`
  (Railing Tags, nhãn Mark) – nằm ngang, phía ngoài nhà, CÓ leader.
- Louver `AV-Lam Thép Logia2 : 1000X2800` (Windows, Type Comments `Louver`) 1051368, Mark `LV-01`, tag family
  `TAG LOUVER MARK` (Window Tags, nhãn Mark trơn) – nằm ngang, phía ngoài nhà.
- Các lan can khác của G19 chưa có Mark; 16 louver còn lại mang Mark số tự tăng (55…70).
- G19 có sẵn sheet trống `A.7-201 CHI TIẾT LOUVER`, `A.7-301 CHI TIẾT LAN CAN` (chi tiết, không phải mặt bằng định vị →
  công cụ không dùng).

## Quy tắc (lõi `scripts\dynamo\LanCanLouver_TuDong.py`)
1. **View**: như nút Định vị + tag cửa / Chống thấm. Mặt bằng tầng đang mở → tầng đã có view tên / template chứa
   "định vị lan can" thì dùng; chưa có thì `sh_tao_view` (khối chung `DatSheet_chung.py`) nhân bản view đang mở (không
   kèm chú thích) thành `MẶT BẰNG ĐỊNH VỊ LAN CAN, LOUVER - <tầng>`, loại view riêng, template cùng tên (tạo từ template
   view gốc: Hidden Line, sàn Halftone tắt mẫu tô, tường xây Halftone, vách / cột BTCT tô đặc, ẩn nội thất / thiết bị cơ
   điện / ký hiệu mặt đứng, mặt cắt, filter ẩn trục link; công cụ ẩn thêm Plumbing Fixtures – IN[14]); crop sát nhà.
2. **Nhận diện theo Mark** (instance `ALL_MODEL_MARK`): tiền tố IN[4] `LK;LC` = lan can, IN[6] `LV` = louver (không
   phân biệt hoa thường / dấu). Đối tượng xét: Railings (mọi Railing = lan can), Windows / Generic Models có Type
   Comments hoặc tên family / type chứa `Louver` / `Lam` (nguyên chữ) = louver, cộng mọi đối tượng Windows / Generic
   Models có Mark đúng tiền tố.
3. **Chỉ tag Mark đúng tiền tố** (IN[24], mặc định bật). Mark trống / sai tiền tố (vd. 55) → không tag, liệt kê "CẦN XEM
   LẠI" để người dùng điền Mark rồi bấm lại.
4. **Family tag**: Railings → IN[1] `AV-Railing Tag- Mark-lan can`; Windows → IN[2] `TAG LOUVER MARK`; Generic Models →
   IN[3] `ARV_Tag Louver Mark GM`. Dự án thiếu → nạp bản đóng gói trong `lib\tag_lan_can\` (cùng tên family mẫu G19 của
   người dùng; `ARV_Tag Louver Mark GM.rfa` là bản đổi hạng mục sang Generic Model Tags). **Luôn nạp** family lan can +
   louver (Windows), và GM nếu view có louver loại đó, KỂ CẢ khi chưa có đối tượng nào đủ Mark để tag (sửa 2026-11-05: bản
   đầu chỉ nạp khi có đối tượng sẽ tag nên model chưa có Mark không nạp gì). Tag xong mà chữ tag ≠ Mark thì báo.
   Hạng mục khác (tường, curtain wall…) mang Mark LK / LV: chỉ liệt kê (Revit 2027.3 KHÔNG đổi được family tag sang
   Multi-Category qua API: "The input category id cannot be assigned").
5. **Vị trí tag** (thuật toán Tag cửa): hệ cục bộ theo đối tượng (lan can: đoạn đường dẫn dài nhất; louver: Hand /
   Facing), dấu chân = hình học trong view. Ưu tiên NGAY GIỮA, phía NGOÀI nhà (dò tia 2 phía, phía trống tới tường xa
   hơn, tối đa 8 m; bằng nhau thì xa tâm khung bao tường), sát mép; rồi
   phía trong; rồi lưới gần (dịch dọc ≤ ½ đối tượng + 2 bề dài tag, lùi ≤ 8 mm giấy). Vật cản: tường, cột, cửa, cửa sổ,
   lan can, louver, cầu thang, tag / chữ có sẵn, tag vừa đặt. Lệch khỏi giữa / lùi > 1 bề cao tag → leader gắn vào đối
   tượng (IN[15] = luôn leader). Tag NẰM NGANG như mẫu (IN[11] = xoay theo phương đối tượng).
6. **Bấm lại không trùng**: đối tượng đã có tag (bất kỳ) trong view thì bỏ qua; IN[10] = dời lại tag đã có cùng family.
7. **Đặt lên bản vẽ** (IN[17] – IN[23], hộp thoại `arv_hoi_sheet.hoi_lan_can_louver` = `_hoi_mat_bang` dời chỉ số 7):
   khung tên theo khổ, giữa vùng vẽ, giữ tỉ lệ view, thu trục; sheet trống có sẵn mang tên "định vị lan can" thì gợi ý số
   hiệu đó; số mặc định tiếp theo trong hạng mục (`A.DVLC.01` khi chưa có). Sau đó 2 bảng thống kê
   `BẢNG THỐNG KÊ LAN CAN <TẦNG>` (Tên / Tổng chiều dài / Chiều cao / Số lượng) và `BẢNG THỐNG KÊ LOUVER <TẦNG>` (Tên /
   Chiều dài / Chiều cao / Số lượng), gộp theo Mark, dòng TỔNG, lọc tầng + Mark BeginsWith tiền tố chung, sát góc phải dưới
   vùng vẽ; bảng cùng tên đã có thì dùng lại. View đã nằm trên sheet từ lần bấm trước thì bổ sung bảng còn thiếu, bảng đã
   đặt giữ nguyên chỗ.
8. Dry-run (IN[5]): đặt thử tag trong SubTransaction rồi huỷ; không tạo view / sheet / nạp family (chỉ báo "sẽ …").

## Nút Thống kê lan can, louver (người dùng yêu cầu 2026-11-05: "thống kê lan can louver như cửa")
- `Archivina` → `HS TKBVTC` → **Thống kê lan can, louver** (`ThongKeLanCan.pushbutton`, sau Thống kê cửa; icon PA1 mdi
  `table-edit`, người dùng duyệt ảnh 2026-11-05). Lõi `scripts\dynamo\ThongKeLanCan_TuDong.py` (+ `.json`, `.dyn`), bảng
  `lib\arv_bang_lan_can.py` (`hoi_thong_ke_lan_can`, viết tay). Thứ tự dùng trên model chưa có Mark: Thống kê (đặt tên) →
  Định vị (tag + bảng lên sheet).
- **Bảng đặt tên**: cột như bảng cửa (Loại / Family : Type / Tên hiện tại / Tên đổi / Chiều dài / Chiều cao / SL mặt bằng /
  SL cả dự án). Khác cửa: tên là MARK của từng đối tượng, không phải Type Mark. 1 dòng = cùng lớp + type + kích thước
  (lan can dài làm tròn 10 mm, cao = Railing Height của type) + Mark đúng tiền tố; Mark trống / sai tiền tố gộp chung để
  đặt tên 1 lần (hiện `75, 76, 80 … (11 Mark)`). Dòng vàng: chưa có Mark đúng tiền tố / tên trùng nhóm khác. Bấm Đổi
  tên: tên sai tiền tố hoặc trùng nhóm khác thì hỏi Yes / No.
- **Ô "cả các tầng khác"** (mặc định tích, nhớ ở `%APPDATA%\pyRevit\ARVTools\ThongKeLanCan.json`): đặt Mark cho cả đối
  tượng cùng nhóm toàn dự án. Nhóm đã có Mark đúng tiền tố khác không bị ghi đè vì khoá nhóm chứa Mark.
- **Bảng Revit**: cùng tên với bảng của nút Định vị; đã có thì CẬP NHẬT cột / lọc / gộp. Lan can Railings, louver theo hạng
  mục có nhiều louver nhất trong view (bộ lọc không có "hoặc", còn lại báo CẦN XEM LẠI); lọc Mark BeginsWith khi chỉ dùng
  1 tiền tố, dùng cả LK + LC thì HasValue.
- Nhiều đối tượng cùng Mark làm Revit thêm cảnh báo `Elements have duplicate "Mark" values`: bản sao L3-32 từ 0 lên 8
  (đúng 8 nhóm có > 1 cái). Hệ quả của việc gộp theo Mark, không chặn; chưa báo người dùng xử lý gì thêm.

## Tệp
- Lõi `scripts\dynamo\LanCanLouver_TuDong.py` (25 ô IN). Khối "PHẦN CHUNG ĐẶT SHEET" chép từ `DatSheet_chung.py` bằng
  `python scripts\dynamo\gop_dat_sheet.py` – không sửa tay khối đó. Spec `LanCanLouver_TuDong.json` → `.dyn` bằng
  `build_dyn.py`.
- Family tag đóng gói: `scripts\pyrevit\ARVTools.extension\lib\tag_lan_can\` (bản tên `ARV_Tag Lan Can Mark` / `ARV_Tag
  Louver Mark` cũ đã chuyển vào `_backup\tag_lan_can_20261105_1029\`).
- Hộp thoại: `lib\arv_hoi_sheet.py` → `hoi_lan_can_louver` (thêm 2026-11-05; `_hoi_mat_bang` có thêm tham số
  `nhan_dat`, mặc định giữ chữ cũ cho Chống thấm / Ngăn cháy lan).
- Nút: `Archivina` → `HS TKBVTC` → **Định vị lan can, louver** (thư mục `HoSo.panel\LanCanLouver.pushbutton`, ngay sau
  Định vị + tag cửa; FILE SINH, không sửa tay). Người dùng duyệt ảnh + chọn icon PA1 (mdi `tag-text-outline`)
  2026-11-05, đã build. Khai báo trong `BUTTONS` + `MOT_CHAM` của `build_from_dynamo.py` (`hoi` =
  `arv_hoi_sheet.hoi_lan_can_louver`), icon `scripts\pyrevit\icons\LanCanLouver(.dark).png`. Sinh lại:
  `python scripts\pyrevit\build_from_dynamo.py "<gốc>\file mau revit\dynamo" --chi LanCanLouver`. Revit phải Reload
  pyRevit mới thấy nút. Shift+bấm = hộp thoại 25 ô (Dry-run).
- Log: `Documents\ARV_Logs\lan_can_louver\lan_can_louver_<ngày giờ>_<view id>.txt` (báo cáo + chi tiết vị trí).

## Thử (bản sao G19, `_tmp\revit_lancan\`)
- Khảo sát chỉ đọc: `khaosat\` (`ket_qua.txt`).
- Thử lõi: `thu1\chay_thu.py` (dựng 3 family đóng gói vào `thu1\goi\`; gán Mark THỬ trên bản sao: lan can theo chiều dài
  LK-01…07, louver theo type LV-01…03; rồi hộp thoại → Dry-run → chạy → chạy lần 2), chạy bằng
  `_tmp\revit_g19\chay_dynamo_ui.ps1` (~3 phút).
- Kết quả 2026-11-05 (lần 4, `thu1\`): từ view `Tầng 1` tạo view + template + loại view, 21 lan can + 17 louver tag đúng
  Mark, tất cả phía ngoài nhà, 0 đè, 0 leader; sheet `A.DVLC.01` khung `AV-Khung A1(841x594)-Kien Truc`, 2 bảng thống
  kê; bấm lần 2: 0 tag mới, không đặt sheet thêm. G19 mặt bằng kể cả trục 702 mm > vùng vẽ 681 mm và chạm bảng góc phải
  dưới (lõi báo CẦN XEM LẠI) – như các công cụ khác trên G19. Ảnh `thu1\xem_sheet.png`, `xem_san_trong.png`, bản lưu
  `G19_lan_can_louver_thu.rvt`. Lần 1–3 (`lan1\`–`lan3\`) để so.
- Bấm NÚT THẬT qua journal (`_tmp\pyrevit_lancan\`, nút thử `ARVTestLC`, xong đã gỡ khỏi Extension Search Path) trên
  bản sao G19 Mark GỐC: tạo view + sheet A.DVLC.01, tag `LK-01` + `LV-01`, liệt kê 20 lan can chưa có Mark + 16 louver
  Mark số (55…70); bấm lần 2 không thêm. Người dùng chưa bấm trong Revit của mình (`Cần xác nhận lại`).

- Sửa 2026-11-05 trưa, thử bản sao model thật L3-32 (chưa có 2 family, 17 lan can chưa Mark, 17 louver Mark số):
  - Lõi (`_tmp\revit_lancan\thu2\`, Dynamo): nạp đủ 2 family dù tag 0; 6 + 3 dòng đặt tên; 34 tag đúng chữ, 0 đè; bấm lại
    không trùng.
  - NÚT THẬT qua journal (`_tmp\pyrevit_lancan\ext2\` nút `ARVTestLK`, `journal2.txt`, `kq2\`; đã gỡ khỏi Extension Search
    Path): Định vị (nạp family, sheet A.DVLC.01, chưa bảng) → Thống kê → Định vị (34 tag, 2 bảng vào sheet đã có) → bấm
    lại 2 nút từ view định vị không trùng. Người dùng chưa bấm trong Revit của mình (`Cần xác nhận lại`).

## Bẫy đã gặp
- Thử nhánh nạp family phải dùng model KHÔNG có family: G19 có sẵn nên lần thử đầu không chạy tới nhánh này.
- Phía ngoài theo TÂM NHÀ sai với nhà chữ U (logia nhìn ra sân trong bị tag vào trong căn) → dò tia 2 phía tới tường gần
  nhất (giao tia – cạnh chính xác; dò bước 100 mm nhảy qua tường mỏng), phía trống xa hơn là ngoài; bỏ tường chứa điểm
  giữa đối tượng (gờ dưới lan can).
- Khung bao family cửa sổ (`get_BoundingBox(view)`) lớn hơn hình thật, chặn oan chỗ đặt tag → cửa / cửa sổ dùng dấu chân
  hình học theo (Hand, Facing).
- `Family.FamilyCategory` = Multi-Category Tags báo "The input category id cannot be assigned" (Window Tags → Railing /
  Generic Model Tags thì được, nhãn Mark giữ nguyên). Lỗi giữa transaction family thì phải RollBack trước `Close`.
- PythonNet3: `Element.Name.GetValue(type)` lỗi 'PropertyObject' trong script thử → đọc `SYMBOL_NAME_PARAM`.
- Bảng lan can bỏ cột Loại (tên railing type dài, bảng tràn sang mặt bằng).
