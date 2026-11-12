---
name: bo-dynamo-arv-file-mau
description: Bộ 20 công cụ Dynamo ARV_*_v1 (dựng model Revit từ DWG link) ở D:\AI\file mau revit\dynamo — xem trước khi viết graph Revit mới
metadata:
  node_type: memory
  type: reference
  originSessionId: 1934bfca-461b-438f-bb4a-fa3f3b7aabf0
  modified: 2026-10-27T10:26:47.953Z
---

`D:\AI\file mau revit\dynamo\` có 20 công cụ Dynamo `ARV_<Chức năng>_v1.dyn` + `.py` (mã Python node; sửa `.py` thì phải cập nhật lại node trong `.dyn`). Mô tả + trạng thái trong `README.md` của thư mục đó (đọc lại khi cần chi tiết). Người dùng dặn ghi nhớ và áp dụng (2026-10-27).

Nhóm:
- Kết cấu / trục: TaoTrucTuCSV (thực ra đọc CAD lưới trục), TaoCotVachTuCAD, TaoDamTuCAD (nhãn bxh), VeBaoSanTuCAD (bao sàn + sàn KC), CatTuongTheoDamSan.
- Kiến trúc: TaoTuongTuCAD, TaoCuaTuCAD, TaoCuaSoTuCAD, TaoGoLogia (VBT-150), TaoLanCanLouverLogia.
- Hoàn thiện căn hộ: TaoSanHoanThien (DWG có hatch sàn), TaoSanCanHoTuCAD (chưa có hatch; sàn `ARV-SanCanHo`), TaoTranCanHo, OpTuongWC (cao 2400), TaoLenGo (`LCT-Gỗ`), TaoLenGachLogia (`LCT-Gạch`), DanTrangCanHo (Room + sheet CTCH A1).
- WC / CTN: TaoThietBiWCTuCAD, TaoOngThoatNuocWC (toạ độ nhập tay), TaoOngThoatNuocTuCAD.
- Ngoài README: `TaoSanKetCau.dyn` (chưa rõ vai trò). `data\`, `families\` trống.

**How to apply:**
- Khi người dùng nhờ việc Revit/Dynamo thuộc các nhóm trên: kiểm tra công cụ có sẵn ở đây trước, dùng lại / học cách dò CAD của nó, không viết mới từ đầu.
- Cả 20 công cụ "Chưa duyệt"; viết cho Revit 2026 (máy khác). Máy này Revit 2027 + PythonNet3 → chạy thử trên bản sao `_tmp` theo [[revit-2027-dynamo-tu-dong]], kiểm `isinstance` lớp Revit / `IntegerValue` trước khi chạy.
- Đọc DWG từ Revit: các tool gọi Core Console qua `core_env()` (môi trường sạch) vì Path của Revit làm accoreconsole lỗi "Unable to load the Modeler DLLs" — giữ cách này khi viết tool mới.
- Thư mục này là file mẫu: sửa thì sao lưu vào `_backup\` trước, không xoá.
- Có thêm ARV_TaoOngGioTuCAD_v1 (21 tool). Đã chuyển sang pyRevit (2026-10-27, người dùng yêu cầu): xem [[pyrevit-arvtools-revit2027]]. Sửa `.py` gốc thì sinh lại nút bằng `scripts\pyrevit\build_from_dynamo.py`.
