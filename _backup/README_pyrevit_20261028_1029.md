# pyRevit – ARVTools.extension (tab **ARV Tools**)

21 công cụ chuyển từ bộ graph Dynamo `ARV_*_v1` (`file mau revit\dynamo\`) + nút Chống thấm, tổng 22 nút pyRevit. TRẠNG THÁI: **CHƯA DUYỆT** (như bản Dynamo).

Yêu cầu: **pyRevit ≥ 6.5.5** gắn vào Revit 2027. pyRevit 6.4 lỗi engine CPython trên Revit 2027 (`The input string '3.12.3' was not in a correct format` trong `CPythonEngine.GetPythonDll`) → mọi nút báo "Revit could not complete the external command". Cấu hình `cpyengine = 3123` (engine `CPY3123` đi kèm pyRevit).

## Cách hoạt động
- Mỗi nút `ARV Tools.tab\<Panel>.panel\<Tên>.pushbutton\` gồm:
  - `core.py`: nguyên văn mã Python node của graph (chép từ `ARV_<Tên>_v1.py`), logic không đổi.
  - `inputs.json`: các ô `IN[i]` (nhãn lấy từ chú thích đầu file, giá trị mặc định lấy từ Input node trong `.dyn`).
  - `script.py`, `bundle.yaml`: vỏ pyRevit (engine CPython 3, dòng `#! python3`).
- `lib\arv_dynamo_host.py` thay phần Dynamo: hộp thoại nhập `IN[i]`, `DocumentManager` / `TransactionManager` giả, in `OUT` ra cửa sổ báo cáo pyRevit. Phần xem trước hình học của Dynamo (ProtoGeometry) không có trong pyRevit nên bỏ qua; báo cáo chữ và file log giữ nguyên.
  - `List[T](list Python)` không chạy được trong pythonnet của pyRevit (vd. `List[BuiltInCategory]([...])` báo "'list' value cannot be converted") → thư viện thay `List` khi nạp `core.py` bằng bản tạo List rỗng rồi `Add` từng phần tử (cùng kết quả như trong Dynamo).
  - Chạy thử tự động: đặt biến môi trường `ARV_TOOLS_AUTO_REPORT=<file .txt>` trước khi mở Revit → bấm nút không hiện hộp thoại, chạy dry-run với giá trị mặc định, ghi báo cáo vào file đó.
- **Không sửa tay** các file trong `ARVTools.extension\ARV Tools.tab\`. Sửa `.py` / `.dyn` gốc rồi sinh lại:
  ```
  D:\AI\_tools\venv\Scripts\python.exe build_from_dynamo.py "D:\AI\file mau revit\dynamo"
  ```

## Dùng trong Revit
1. Mở Revit 2027 → tab **ARV Tools** (pyRevit đã gắn vào Revit 2027, extension nằm trong Extension Search Path `D:\AI\scripts\pyrevit`). Mới thêm nút thì bấm **pyRevit → Reload**.
2. Bấm nút → hộp thoại liệt kê `IN[0]…IN[n]` như Input node trong Dynamo → **Chạy**.
3. Ô **Dry-run** luôn bật lại mỗi lần mở (chỉ báo cáo, không ghi). Tắt Dry-run để ghi vào mô hình; mọi thay đổi nằm trong 1 Transaction tên `ARV - …` (Ctrl+Z được).
4. Ô có **xoá / làm lại** (chữ đỏ) luôn tắt lại mỗi lần mở; bật khi đã tắt Dry-run thì phải xác nhận thêm một lần.
5. Giá trị đã nhập được nhớ riêng từng máy tại `%APPDATA%\pyRevit\ARVTools\<nút>.json`.

Một số công cụ lấy đối tượng đang chọn (sàn, Room) hoặc level của view đang mở – chọn trước rồi bấm nút, giống khi chạy trong Dynamo.

## Danh sách nút
| Panel | Nút | Graph gốc |
|---|---|---|
| Kết cấu | Tạo trục từ CAD | `ARV_TaoTrucTuCSV_v1` |
| Kết cấu | Cột vách từ CAD | `ARV_TaoCotVachTuCAD_v1` (core lấy bản `.py` mới hơn `.dyn`: có thêm `IN[10]` file `.rfa`) |
| Kết cấu | Dầm từ CAD | `ARV_TaoDamTuCAD_v1` |
| Kết cấu | Bao sàn từ CAD | `ARV_VeBaoSanTuCAD_v1` |
| Kết cấu | Cắt tường theo dầm sàn | `ARV_CatTuongTheoDamSan_v1` |
| Kiến trúc | Tường từ CAD | `ARV_TaoTuongTuCAD_v1` |
| Kiến trúc | Cửa đi từ CAD | `ARV_TaoCuaTuCAD_v1` |
| Kiến trúc | Cửa sổ từ CAD | `ARV_TaoCuaSoTuCAD_v1` |
| Kiến trúc | Gờ logia | `ARV_TaoGoLogia_v1` |
| Kiến trúc | Lan can louver logia | `ARV_TaoLanCanLouverLogia_v1` |
| Hoàn thiện | Sàn hoàn thiện (có hatch) | `ARV_TaoSanHoanThien_v1` |
| Hoàn thiện | Sàn căn hộ từ CAD | `ARV_TaoSanCanHoTuCAD_v1` |
| Hoàn thiện | Trần căn hộ | `ARV_TaoTranCanHo_v1` |
| Hoàn thiện | Ốp tường WC | `ARV_OpTuongWC_v1` |
| Hoàn thiện | Len gỗ | `ARV_TaoLenGo_v1` |
| Hoàn thiện | Len gạch logia | `ARV_TaoLenGachLogia_v1` |
| Hoàn thiện | Dàn trang căn hộ | `ARV_DanTrangCanHo_v1` |
| MEP | Thiết bị WC từ CAD | `ARV_TaoThietBiWCTuCAD_v1` |
| MEP | Ống thoát nước WC | `ARV_TaoOngThoatNuocWC_v1` |
| MEP | Ống thoát nước từ CAD | `ARV_TaoOngThoatNuocTuCAD_v1` |
| MEP | Ống gió từ CAD | `ARV_TaoOngGioTuCAD_v1` |
| Hồ sơ | Chống thấm | `scripts\dynamo\ChongTham_VeVenChanTuong` (nét vén + hatch Filled Region trên view chống thấm; người dùng duyệt trên G19 2026-10-27) |
| Hồ sơ | Ngăn cháy lan | `scripts\dynamo\NganChay_TrucHKT` (hatch Filled Region lưới NET 125 / 45° đỏ trong lòng trục / hộp kỹ thuật trên view chống cháy lan; 2026-10-28, chưa duyệt) |
| Hồ sơ | Lỗ mở shaft | `scripts\dynamo\LoMo_ShaftOpening` (Shaft Opening cho mọi trục / hộp kỹ thuật trên mặt bằng tầng đang mở; file gộp, xem dưới; 2026-10-28) |

**Nút Chống thấm là nút "một chạm"** (người dùng chốt 2026-10-27; khai báo trong `MOT_CHAM` của builder):
- **Bấm**: vẽ luôn vào mô hình, không hộp thoại, không Dry-run (Ctrl+Z một lần là hoàn tác), trên view chống thấm. Người dùng tự tạo view (gán template `1.7 Mặt Bằng Chống thấm`) và tự đặt lên sheet.
  - View đang mở có chữ "chống thấm" trong tên view hoặc tên view template → vẽ vào view đó.
  - Không thì: có đúng 1 view như vậy → vẽ vào view đó rồi chuyển sang view đó; nhiều view → hiện danh sách để chọn; không có view nào → báo, không làm gì.
  - Bấm lại trên view đã vẽ: không vẽ lại vén, không xoá gì, chỉ bổ sung hatch cho phòng chưa có.
- **Shift+bấm** (`config.py`): hộp thoại đầy đủ `IN[0…9]` như các nút khác, Dry-run bật sẵn.
- Giá trị các ô khác (từ khoá sàn, khoảng lùi, line style, thư mục log…) lấy theo lần nhập gần nhất trong hộp thoại Shift+bấm, chưa nhập thì lấy mặc định.
- Đã thử 2026-10-27 (Revit 2027.3 + pyRevit 6.5.5, bản sao G19 chưa vẽ `_backup\G19_20261027_1405.rvt`, chạy nguyên `script.py` của nút khi đang mở view `Tầng 1`): tự chọn view `Level 1 Copy 1 Copy 2`, vẽ 364 nét vén + 59 hatch Filled Region (2 group), ẩn 64 thiết bị; bấm lần 2 không vẽ thêm gì. Kết quả ở `_tmp\pyrevit_chongtham\motcham\kq\`. Chưa thử hộp thoại chọn view (khi có nhiều view chống thấm) và Shift+bấm.

**Nút Ngăn cháy lan cũng là nút một chạm** (2026-10-28), cách chọn view giống Chống thấm nhưng với chữ "cháy lan" (template `1.8 Mặt Bằng Chống Cháy Lan`).
- Đã thử trên bản sao G19 (`_tmp\pyrevit_nganchay\`), bấm khi đang mở `Tầng 1`:
  - tự chọn view `Level 1 Copy 1 Copy 2 Copy 1`;
  - vẽ 38 hatch (group `ARV_NganChay`), ẩn 65 thiết bị;
  - bấm lần 2 không vẽ thêm gì.
- G19 không có ống đứng / shaft / dấu X, nên mọi ô được nhận theo hình học. Bản 2 (sửa theo góp ý người dùng 2026-10-28) **quét lưới 20 mm dấu chân thật của tường** thay cho room tạm:
  - bắt được khe hộp gen ~120 mm, là chỗ room của Revit bỏ sót;
  - nối đầu tường hở ≤ 400 mm, đóng miệng hốc chữ U;
  - bỏ ô > 3 m², tức ô 1770×2520 ở hành lang mà người dùng chỉ là sai.
  
  Người dùng chưa duyệt bản 2 (`Cần xác nhận lại`).

**Bo sát mép tường thô** (người dùng chốt 2026-10-28, áp cho cả Chống thấm và Ngăn cháy lan): vùng hatch và nét bo theo mặt lõi tường, không theo lớp trát / hoàn thiện.
- Chống thấm: room dùng `CoreBoundary`.
- Ngăn cháy lan: quét theo dải lõi tường, rồi bắt cạnh vùng vào đúng mép lõi.
- Khe hộp gen G19 ra đúng 150×800 mm (lõi–lõi).

**Nút Lỗ mở shaft** (2026-10-28, một chạm, làm trên **mặt bằng tầng đang mở**; không mở mặt bằng tầng thì nút báo và không làm gì):
- Tạo Shaft Opening cho mọi trục / hộp kỹ thuật, nhận trục giống hệt nút Ngăn cháy lan (dùng chung hàm `tim_truc`).
- Biên lỗ mở = mép tường thô.
- Base Constraint = Top Constraint = level của mặt bằng; Base Offset -100 mm, Top Offset 1500 mm (người dùng chốt; đổi được qua Shift+bấm).
- Bấm lại: ô đã có shaft opening cắt qua tầng thì bỏ qua, không tạo trùng, không xoá.
- Mã nguồn:
  - `LoMo_ShaftOpening.py` là **file gộp, không sửa tay**. Phần riêng sửa ở `LoMo_ShaftOpening_nguon.py`; quy tắc nhận trục sửa trong khối `PHẦN CHUNG` của `NganChay_TrucHKT.py`.
  - Sau khi sửa thì gộp lại bằng `python scripts\dynamo\gop_lomo_shaft.py`, rồi `build_dyn.py LoMo_ShaftOpening.json` và builder `--chi LoMoShaft`.
- Thử trên bản sao G19 (Tầng 1):
  - 38 lỗ mở, đọc lại đúng Base Tầng 1 / -100, Top Tầng 1 / 1500 (cao độ -100…1500 mm); bấm lần 2 không tạo thêm.
  - Sau đó nút Ngăn cháy lan nhận đủ 38 trục theo bằng chứng shaft opening.
  - Bản lưu `_tmp\pyrevit_lomo\G19_lo_mo_ngan_chay_thu.rvt`. Shaft opening không có tham số Comments.

**Bẫy pythonnet 3.0.3 (CPython của pyRevit), gặp khi làm nút một chạm:**
- Tên nào bị `from Autodesk.Revit.DB import <tên>` **đầu tiên** trong phiên Revit thì bị loại khỏi `from Autodesk.Revit.DB import *` về sau. Ví dụ `lib\arv_dynamo_host.py` import `Transaction, TransactionStatus` trước, nên `core.py` dùng `import *` sẽ thiếu 2 tên này.
  - Đã kiểm chứng: `__all__` còn 1323/1326 tên.
  - Cách tránh: script nút dùng `import Autodesk.Revit.DB as DB`; `core.py` chống thấm bổ sung đủ tên bằng `dir()` ngay sau `import *`.
- `List[T](list Python)` không chạy. Thư viện chỉ thay khi dòng import đúng dạng `from System.Collections.Generic import List`; viết `... import List as NetList` thì không được thay. `core.py` chống thấm tự tạo List rỗng rồi `Add` (hàm `ds_id`).

Nút nguồn ngoài `file mau revit\dynamo` (vd. Chống thấm) khai báo trong `BUTTONS` bằng đường dẫn `../dynamo/<tên>`. Sinh lại riêng 1 nút, không đụng các nút khác:
```
D:\AI\_tools\venv\Scripts\python.exe build_from_dynamo.py "D:\AI\file mau revit\dynamo" --chi ChongTham
```

## Kết quả chạy thử (2026-10-27, Revit 2027.3 + pyRevit 6.5.5, bản sao G19, dry-run)
Mở Revit bằng journal, bấm nút thử chạy lần lượt 22 nút với giá trị mặc định. Không nút nào lỗi phần vỏ pyRevit.
- Chạy hết, ra báo cáo: Chống thấm, Dàn trang căn hộ, Ốp tường WC, Len gạch logia (141 đoạn / 528 viên), Len gỗ, Trần căn hộ, Cắt tường theo dầm sàn, Ống thoát nước WC.
- Dừng đúng kiểm tra đầu vào vì G19 **không có bản CAD link**: Tạo trục, Cột vách, Dầm, Bao sàn, Tường, Cửa đi, Cửa sổ, Gờ logia, Lan can louver, Sàn căn hộ từ CAD, Thiết bị WC, Ống thoát nước từ CAD, Ống gió → phần đọc CAD / Core Console **chưa được thử trong pyRevit** (`Cần xác nhận lại`).
- Sàn hoàn thiện: cần chọn cửa vào căn trước khi bấm → chưa thử phần dựng sàn.
- Chưa thử chế độ ghi thật (Dry-run tắt) trong pyRevit. Hộp thoại đã chụp ảnh kiểm tra (Cửa sổ 18 ô, Dàn trang có ô xoá chữ đỏ).

## Giới hạn đã biết
- Các công cụ đọc chữ trong DWG gọi AutoCAD Core Console (`C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe`, lấy bản mới nhất) – máy không có AutoCAD thì công cụ báo dừng hoặc đặt tên tự động.
- Giá trị mặc định trong `inputs.json` là giá trị đang đặt trong `.dyn` (dự án G19: level `Tầng 1`, tên type `AV-…`, đường dẫn template MEP `C:\ProgramData\Autodesk\RVT 20…`) – dự án khác phải sửa trong hộp thoại.
- Extension `ARV.extension` cũ ở `D:\AI REVIT\tools\pyrevit` (tab **ARV**, 4 nút) vẫn được nạp song song, không đụng tới.
