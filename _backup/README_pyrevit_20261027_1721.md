# pyRevit – ARVTools.extension (tab **ARV Tools**)

21 công cụ chuyển từ bộ graph Dynamo `ARV_*_v1` (`file mau revit\dynamo\`) sang nút pyRevit. TRẠNG THÁI: **CHƯA DUYỆT** (như bản Dynamo).

## Cách hoạt động
- Mỗi nút `ARV Tools.tab\<Panel>.panel\<Tên>.pushbutton\` gồm:
  - `core.py`: nguyên văn mã Python node của graph (chép từ `ARV_<Tên>_v1.py`), logic không đổi.
  - `inputs.json`: các ô `IN[i]` (nhãn lấy từ chú thích đầu file, giá trị mặc định lấy từ Input node trong `.dyn`).
  - `script.py`, `bundle.yaml`: vỏ pyRevit (engine CPython 3, dòng `#! python3`).
- `lib\arv_dynamo_host.py` thay phần Dynamo: hộp thoại nhập `IN[i]`, `DocumentManager` / `TransactionManager` giả, in `OUT` ra cửa sổ báo cáo pyRevit. Phần xem trước hình học của Dynamo (ProtoGeometry) không có trong pyRevit nên bỏ qua; báo cáo chữ và file log giữ nguyên.
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

## Giới hạn đã biết
- Các công cụ đọc chữ trong DWG gọi AutoCAD Core Console (`C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe`, lấy bản mới nhất) – máy không có AutoCAD thì công cụ báo dừng hoặc đặt tên tự động.
- Giá trị mặc định trong `inputs.json` là giá trị đang đặt trong `.dyn` (dự án G19: level `Tầng 1`, tên type `AV-…`, đường dẫn template MEP `C:\ProgramData\Autodesk\RVT 20…`) – dự án khác phải sửa trong hộp thoại.
- Extension `ARV.extension` cũ ở `D:\AI REVIT\tools\pyrevit` (tab **ARV**, 4 nút) vẫn được nạp song song, không đụng tới.
